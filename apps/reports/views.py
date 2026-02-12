from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg, Max, Min, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.http import JsonResponse, HttpResponse
import json

# Import models
from apps.customers.models import Customer
from apps.orders.models import (
    PurchaseOrder, Invoice, InvoicePayment, Receipt,
    ReturnInvoice, Proforma, SampleOrder, Sickness
)
from apps.workers.models import Worker
from apps.branches.models import Branch
from apps.stock.models import Stock
from apps.products.models import Product

from web_project import TemplateLayout
from .models import SavedReport, ReportExport, ReportAccessLog


def manager_required(view_func):
    """Decorator to restrict access to management roles"""
    def wrapper(request, *args, **kwargs):
        # Allow superusers
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, 'worker_profile'):
            messages.error(request, "Access denied. Management access required.")
            return redirect('index')

        worker = request.user.worker_profile
        allowed_roles = [
            'Director General', 'Marketing Director',
            'Central Stock Manager', 'Human Resource',
            'Accountant', 'Pharmacist'
        ]

        if worker.role not in allowed_roles:
            messages.error(request, "Access denied. Management role required.")
            return redirect('index')

        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@manager_required
def reports_dashboard(request):
    """Main reports dashboard with overview metrics"""

    # Get date filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')

    # Default to last 30 days if no dates provided
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # Base querysets
    invoices_qs = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )

    if branch_filter:
        invoices_qs = invoices_qs.filter(branch_id=branch_filter)

    # Calculate KPIs
    total_revenue = invoices_qs.aggregate(
        total=Coalesce(Sum('total_with_taxes'), Decimal('0.00'))
    )['total']

    total_outstanding = invoices_qs.aggregate(
        outstanding=Coalesce(Sum('amount_due'), Decimal('0.00'))
    )['outstanding']

    total_paid = invoices_qs.aggregate(
        paid=Coalesce(Sum('amount_paid'), Decimal('0.00'))
    )['paid']

    total_customers = Customer.objects.count()
    active_customers = invoices_qs.values('customer').distinct().count()

    total_orders = PurchaseOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).count()

    # Top 5 customers by revenue
    top_customers = invoices_qs.values(
        'customer__id',
        'customer__customer_name',
        'customer__customer_id'
    ).annotate(
        total_revenue=Sum('total_with_taxes'),
        total_debt=Sum('amount_due')
    ).order_by('-total_revenue')[:5]

    # Revenue by branch
    revenue_by_branch = invoices_qs.values(
        'branch__branch_name'
    ).annotate(
        revenue=Sum('total_with_taxes'),
        debt=Sum('amount_due')
    ).order_by('-revenue')

    # Top performing sales reps
    top_sales_reps = invoices_qs.values(
        'sales_rep__employee_id',
        'sales_rep__user__first_name',
        'sales_rep__user__last_name'
    ).annotate(
        total_sales=Sum('total_with_taxes'),
        order_count=Count('id')
    ).order_by('-total_sales')[:10]

    # Daily revenue trend (last 30 days)
    daily_revenue = invoices_qs.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_with_taxes')
    ).order_by('date')

    # Convert to JSON-safe format
    daily_revenue_data = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue'] or 0)
        }
        for item in daily_revenue
    ]

    # Payment method breakdown
    payment_breakdown_qs = InvoicePayment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to
    )
    if branch_filter:
        payment_breakdown_qs = payment_breakdown_qs.filter(invoice__branch_id=branch_filter)

    payment_breakdown = payment_breakdown_qs.values('payment_mode').annotate(
        total=Sum('amount_paid')
    ).order_by('-total')

    # If no payment records exist, fall back to payment modes from orders
    if not payment_breakdown.exists():
        payment_breakdown_qs = PurchaseOrder.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
            payment_mode__isnull=False
        )
        if branch_filter:
            payment_breakdown_qs = payment_breakdown_qs.filter(branch_id=branch_filter)

        payment_breakdown = payment_breakdown_qs.values('payment_mode').annotate(
            total=Sum('grand_total')
        ).order_by('-total')

    # Convert to JSON-safe format
    payment_breakdown_data = [
        {
            'payment_mode': item['payment_mode'],
            'total': float(item['total'] or 0)
        }
        for item in payment_breakdown
    ]

    # Get all branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'total_revenue': total_revenue,
        'total_outstanding': total_outstanding,
        'total_paid': total_paid,
        'collection_rate': (total_paid / total_revenue * 100) if total_revenue > 0 else 0,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_orders': total_orders,
        'top_customers': top_customers,
        'revenue_by_branch': revenue_by_branch,
        'top_sales_reps': top_sales_reps,
        'daily_revenue': json.dumps(daily_revenue_data),
        'payment_breakdown': json.dumps(payment_breakdown_data),
        'branches': branches,
        'date_from': date_from,
        'date_to': date_to,
        'selected_branch': branch_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/dashboard.html', context)


@login_required
@manager_required
def client_financial_report(request):
    """Detailed financial report for all clients"""

    # Get filters
    search_query = request.GET.get('search', '')
    branch_filter = request.GET.get('branch')
    debt_filter = request.GET.get('debt_status')  # 'with_debt', 'no_debt', 'all'
    sort_by = request.GET.get('sort', '-total_debt')

    # Base queryset
    customers = Customer.objects.all()

    if search_query:
        customers = customers.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_id__icontains=search_query)
        )

    if branch_filter:
        customers = customers.filter(branch_id=branch_filter)

    # Annotate with financial data
    customers = customers.annotate(
        total_orders=Count('purchaseorder'),
        total_invoices=Count('invoice'),
        total_revenue=Coalesce(Sum('invoice__total_with_taxes'), Decimal('0.00')),
        total_paid=Coalesce(Sum('invoice__amount_paid'), Decimal('0.00')),
        total_debt=Coalesce(Sum('invoice__amount_due'), Decimal('0.00')),
        last_order_date=Max('purchaseorder__created_at')
    )

    # Apply debt filter
    if debt_filter == 'with_debt':
        customers = customers.filter(total_debt__gt=0)
    elif debt_filter == 'no_debt':
        customers = customers.filter(total_debt=0)

    # Sort
    customers = customers.order_by(sort_by)

    # Calculate totals from base Invoice queryset
    base_invoices = Invoice.objects.filter(customer__in=customers.values_list('id', flat=True))
    if branch_filter:
        base_invoices = base_invoices.filter(branch_id=branch_filter)

    totals = base_invoices.aggregate(
        total_revenue=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_debt=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_paid=Coalesce(Sum('amount_paid'), Decimal('0.00'))
    )

    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'customers': customers,
        'totals': totals,
        'branches': branches,
        'search_query': search_query,
        'selected_branch': branch_filter,
        'debt_filter': debt_filter,
        'sort_by': sort_by,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/client_financial.html', context)


@login_required
@manager_required
def client_detail_report(request, customer_id):
    """Detailed financial report for a specific client"""

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        messages.error(request, "Customer not found.")
        return redirect('client_financial_report')

    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # All invoices for this customer
    invoices_qs = Invoice.objects.filter(customer=customer)

    if date_from:
        invoices_qs = invoices_qs.filter(created_at__date__gte=date_from)
    if date_to:
        invoices_qs = invoices_qs.filter(created_at__date__lte=date_to)

    invoices = invoices_qs.order_by('-created_at')

    # Payment history
    payments = InvoicePayment.objects.filter(
        invoice__customer=customer
    ).order_by('-payment_date')

    # Financial summary
    financial_summary = invoices_qs.aggregate(
        total_invoices=Count('id'),
        total_amount=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_paid=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00'))
    )

    # Order history
    orders = PurchaseOrder.objects.filter(
        customer=customer
    ).order_by('-created_at')[:20]

    # Monthly revenue trend
    monthly_trend_raw = invoices_qs.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_with_taxes'),
        paid=Sum('amount_paid'),
        outstanding=Sum('amount_due')
    ).order_by('month')

    # Convert to JSON-safe format
    monthly_trend = [
        {
            'month': item['month'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue'] or 0),
            'paid': float(item['paid'] or 0),
            'outstanding': float(item['outstanding'] or 0)
        }
        for item in monthly_trend_raw
    ]

    view_context = {
        'customer': customer,
        'invoices': invoices,
        'payments': payments,
        'financial_summary': financial_summary,
        'orders': orders,
        'monthly_trend': json.dumps(monthly_trend),
        'date_from': date_from,
        'date_to': date_to,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/client_detail.html', context)


@login_required
@manager_required
def regional_performance_report(request):
    """Performance report by region/branch"""

    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # Branch performance
    branches = Branch.objects.filter(is_active=True).annotate(
        total_customers=Count('customers', distinct=True),
        total_orders=Count(
            'purchaseorder',
            filter=Q(
                purchaseorder__created_at__date__gte=date_from,
                purchaseorder__created_at__date__lte=date_to
            )
        ),
        total_revenue=Coalesce(
            Sum(
                'invoice__total_with_taxes',
                filter=Q(
                    invoice__created_at__date__gte=date_from,
                    invoice__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        ),
        total_debt=Coalesce(
            Sum(
                'invoice__amount_due',
                filter=Q(
                    invoice__created_at__date__gte=date_from,
                    invoice__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        ),
        total_paid=Coalesce(
            Sum(
                'invoice__amount_paid',
                filter=Q(
                    invoice__created_at__date__gte=date_from,
                    invoice__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        ),
        active_sales_reps=Count('workers', filter=Q(workers__role='Sales Rep'), distinct=True)
    ).order_by('-total_revenue')

    # Calculate totals from base invoices
    base_invoices = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    totals = base_invoices.aggregate(
        total_revenue=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_debt=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_orders=Count('id')
    )

    # Regional comparison chart data
    regional_data = [
        {
            'branch_name': branch.branch_name,
            'total_revenue': float(branch.total_revenue or 0),
            'total_debt': float(branch.total_debt or 0),
            'total_orders': branch.total_orders or 0
        }
        for branch in branches
    ]

    view_context = {
        'branches': branches,
        'totals': totals,
        'regional_data': json.dumps(regional_data),
        'date_from': date_from,
        'date_to': date_to,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/regional_performance.html', context)


@login_required
@manager_required
def sales_agent_performance_report(request):
    """Performance report by sales agent"""

    # Get filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # Sales rep performance
    sales_reps = Worker.objects.filter(
        role='Sales Rep',
        is_active=True
    )

    if branch_filter:
        sales_reps = sales_reps.filter(branch_id=branch_filter)

    sales_reps = sales_reps.annotate(
        total_customers=Count('customers', distinct=True),
        total_orders=Count(
            'sales_rep_orders',
            filter=Q(
                sales_rep_orders__created_at__date__gte=date_from,
                sales_rep_orders__created_at__date__lte=date_to
            )
        ),
        total_revenue=Coalesce(
            Sum(
                'invoice_sales_rep_orders__total_with_taxes',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        ),
        total_collected=Coalesce(
            Sum(
                'invoice_sales_rep_orders__amount_paid',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        ),
        total_outstanding=Coalesce(
            Sum(
                'invoice_sales_rep_orders__amount_due',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )
            ),
            Decimal('0.00')
        )
    ).order_by('-total_revenue')

    # Calculate totals from base invoices
    base_invoices = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        sales_rep__role='Sales Rep',
        sales_rep__is_active=True
    )
    if branch_filter:
        base_invoices = base_invoices.filter(sales_rep__branch_id=branch_filter)

    totals = base_invoices.aggregate(
        total_revenue=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_collected=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_orders=Count('id')
    )

    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'sales_reps': sales_reps,
        'totals': totals,
        'branches': branches,
        'date_from': date_from,
        'date_to': date_to,
        'selected_branch': branch_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/sales_agent_performance.html', context)


@login_required
@manager_required
def financial_summary_report(request):
    """Comprehensive financial summary"""

    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    view_type = request.GET.get('view', 'daily')  # daily, weekly, monthly

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # Revenue summary
    invoices_qs = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )

    revenue_summary = invoices_qs.aggregate(
        total_invoices=Count('id'),
        gross_revenue=Coalesce(Sum('grand_total'), Decimal('0.00')),
        total_with_taxes=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_collected=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00'))
    )

    # Payment analysis
    payments = InvoicePayment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to
    )

    payment_by_method = payments.values('payment_mode').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-total')

    # Cash vs Credit analysis
    cash_credit = PurchaseOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('payment_method').annotate(
        total=Sum('grand_total'),
        count=Count('id')
    )

    # Trend analysis
    if view_type == 'daily':
        trend_data_raw = invoices_qs.annotate(
            period=TruncDate('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('period')
    elif view_type == 'weekly':
        trend_data_raw = invoices_qs.annotate(
            period=TruncWeek('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('period')
    else:  # monthly
        trend_data_raw = invoices_qs.annotate(
            period=TruncMonth('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('period')

    # Convert to JSON-safe format
    trend_data = [
        {
            'period': item['period'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue'] or 0),
            'collected': float(item['collected'] or 0),
            'outstanding': float(item['outstanding'] or 0)
        }
        for item in trend_data_raw
    ]

    # Outstanding invoices aging
    today = timezone.now().date()

    aging_analysis = {
        '0-30': invoices_qs.filter(
            amount_due__gt=0,
            created_at__date__gte=today - timedelta(days=30)
        ).aggregate(
            count=Count('id'), total=Coalesce(Sum('amount_due'), Decimal('0.00'))
        ),
        '31-60': invoices_qs.filter(
            amount_due__gt=0,
            created_at__date__lt=today - timedelta(days=30),
            created_at__date__gte=today - timedelta(days=60)
        ).aggregate(
            count=Count('id'), total=Coalesce(Sum('amount_due'), Decimal('0.00'))
        ),
        '61-90': invoices_qs.filter(
            amount_due__gt=0,
            created_at__date__lt=today - timedelta(days=60),
            created_at__date__gte=today - timedelta(days=90)
        ).aggregate(
            count=Count('id'), total=Coalesce(Sum('amount_due'), Decimal('0.00'))
        ),
        '90+': invoices_qs.filter(
            amount_due__gt=0,
            created_at__date__lt=today - timedelta(days=90)
        ).aggregate(
            count=Count('id'), total=Coalesce(Sum('amount_due'), Decimal('0.00'))
        ),
    }

    view_context = {
        'revenue_summary': revenue_summary,
        'payment_by_method': list(payment_by_method),
        'cash_credit': list(cash_credit),
        'trend_data': json.dumps(trend_data),
        'aging_analysis': aging_analysis,
        'date_from': date_from,
        'date_to': date_to,
        'view_type': view_type,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/financial_summary.html', context)


@login_required
@manager_required
def debt_analysis_report(request):
    """Detailed debt and outstanding receivables analysis"""

    # Get filters
    branch_filter = request.GET.get('branch')
    age_filter = request.GET.get('age')  # current, 30, 60, 90, overdue

    # Outstanding invoices
    today = timezone.now().date()

    outstanding_invoices = Invoice.objects.filter(
        amount_due__gt=0
    ).select_related('customer', 'branch', 'sales_rep')

    if branch_filter:
        outstanding_invoices = outstanding_invoices.filter(branch_id=branch_filter)

    # Apply age filter
    if age_filter == '0-30':
        outstanding_invoices = outstanding_invoices.filter(created_at__date__gte=today - timedelta(days=30))
    elif age_filter == '31-60':
        outstanding_invoices = outstanding_invoices.filter(
            created_at__date__lt=today - timedelta(days=30),
            created_at__date__gte=today - timedelta(days=60)
        )
    elif age_filter == '61-90':
        outstanding_invoices = outstanding_invoices.filter(
            created_at__date__lt=today - timedelta(days=60),
            created_at__date__gte=today - timedelta(days=90)
        )
    elif age_filter == '90+':
        outstanding_invoices = outstanding_invoices.filter(created_at__date__lt=today - timedelta(days=90))

    # Order by created_at (oldest first)
    outstanding_invoices_list = list(outstanding_invoices.order_by('created_at'))

    # Add days_outstanding attribute to each invoice
    for invoice in outstanding_invoices_list:
        invoice.days_outstanding = (today - invoice.created_at.date()).days

    # Summary statistics
    debt_summary = {
        'total_outstanding': sum(inv.amount_due for inv in outstanding_invoices_list),
        'total_invoices': len(outstanding_invoices_list),
        'avg_outstanding': sum(inv.amount_due for inv in outstanding_invoices_list) / len(outstanding_invoices_list) if outstanding_invoices_list else 0,
        'oldest_debt_days': max((inv.days_outstanding for inv in outstanding_invoices_list), default=0),
    }

    # Top debtors
    top_debtors = Customer.objects.annotate(
        total_debt=Coalesce(Sum('invoice__amount_due', filter=Q(invoice__amount_due__gt=0)), Decimal('0.00'))
    ).filter(total_debt__gt=0).order_by('-total_debt')[:20]

    # Debt by branch
    debt_by_branch = Branch.objects.annotate(
        total_debt=Coalesce(Sum('invoice__amount_due', filter=Q(invoice__amount_due__gt=0)), Decimal('0.00')),
        invoice_count=Count('invoice', filter=Q(invoice__amount_due__gt=0))
    ).filter(total_debt__gt=0).order_by('-total_debt')

    # Debt by sales rep
    debt_by_rep = Worker.objects.filter(role='Sales Rep').annotate(
        total_debt=Coalesce(
            Sum('invoice_sales_rep_orders__amount_due', filter=Q(invoice_sales_rep_orders__amount_due__gt=0)),
            Decimal('0.00')
        ),
        invoice_count=Count('invoice_sales_rep_orders', filter=Q(invoice_sales_rep_orders__amount_due__gt=0))
    ).filter(total_debt__gt=0).order_by('-total_debt')

    # Get branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'outstanding_invoices': outstanding_invoices_list,
        'debt_summary': debt_summary,
        'top_debtors': top_debtors,
        'debt_by_branch': debt_by_branch,
        'debt_by_rep': debt_by_rep,
        'branches': branches,
        'selected_branch': branch_filter,
        'age_filter': age_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/debt_analysis.html', context)


# Export functionality (stub for now - will implement Excel/PDF export)
@login_required
@manager_required
def export_report(request, report_type):
    """Export report to Excel or PDF"""
    export_format = request.GET.get('format', 'excel')

    # TODO: Implement actual export logic
    messages.info(request, f"Export functionality for {report_type} coming soon!")

    return redirect('reports_dashboard')
