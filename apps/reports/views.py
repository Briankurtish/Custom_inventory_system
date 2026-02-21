from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg, Max, Min, DecimalField, ExpressionWrapper
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

    # Base querysets - ALL TIME by default
    invoices_qs = Invoice.objects.all()

    # Apply date filters only if provided
    if date_from:
        invoices_qs = invoices_qs.filter(created_at__date__gte=date_from)
    if date_to:
        invoices_qs = invoices_qs.filter(created_at__date__lte=date_to)

    if branch_filter:
        invoices_qs = invoices_qs.filter(branch_id=branch_filter)

    # OPTIMIZED: Combine KPI calculations in one query
    kpis = invoices_qs.aggregate(
        total_revenue=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_paid=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        active_customers=Count('customer', distinct=True)
    )
    
    total_revenue = kpis['total_revenue']
    total_outstanding = kpis['total_outstanding']
    total_paid = kpis['total_paid']
    active_customers = kpis['active_customers']
    
    # Get total customers (cached simple count)
    total_customers = Customer.objects.count()

    # Total orders with conditional date filtering
    orders_qs = PurchaseOrder.objects.all()
    if date_from:
        orders_qs = orders_qs.filter(created_at__date__gte=date_from)
    if date_to:
        orders_qs = orders_qs.filter(created_at__date__lte=date_to)
    if branch_filter:
        orders_qs = orders_qs.filter(branch_id=branch_filter)

    total_orders = orders_qs.count()

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

    # Daily revenue trend - OPTIMIZED: Limit to last 90 days max
    trend_start = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    trend_invoices = invoices_qs.filter(created_at__date__gte=trend_start)
    
    daily_revenue = trend_invoices.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_with_taxes')
    ).order_by('date')[:90]  # Limit to 90 data points

    # Convert to JSON-safe format
    daily_revenue_data = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'revenue': float(item['revenue'] or 0)
        }
        for item in daily_revenue
    ]

    # Payment method breakdown
    payment_breakdown_qs = InvoicePayment.objects.all()
    if date_from:
        payment_breakdown_qs = payment_breakdown_qs.filter(payment_date__date__gte=date_from)
    if date_to:
        payment_breakdown_qs = payment_breakdown_qs.filter(payment_date__date__lte=date_to)
    if branch_filter:
        payment_breakdown_qs = payment_breakdown_qs.filter(invoice__branch_id=branch_filter)

    payment_breakdown = payment_breakdown_qs.values('payment_mode').annotate(
        total=Sum('amount_paid')
    ).order_by('-total')

    # If no payment records exist, fall back to payment modes from orders
    if not payment_breakdown.exists():
        payment_breakdown_qs = PurchaseOrder.objects.filter(payment_mode__isnull=False)
        if date_from:
            payment_breakdown_qs = payment_breakdown_qs.filter(created_at__date__gte=date_from)
        if date_to:
            payment_breakdown_qs = payment_breakdown_qs.filter(created_at__date__lte=date_to)
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
    """Detailed financial report for all clients - OPTIMIZED"""

    # Get filters
    search_query = request.GET.get('search', '')
    branch_filter = request.GET.get('branch')
    debt_filter = request.GET.get('debt_status')  # 'with_debt', 'no_debt', 'all'
    sort_by = request.GET.get('sort', '-total_debt')

    # OPTIMIZED: Use only() to fetch only needed fields, keep as model instances for template compatibility
    customers = Customer.objects.select_related('branch', 'sales_rep').only(
        'id', 'customer_id', 'customer_name', 
        'branch__branch_name', 
        'sales_rep__employee_id', 'sales_rep__user__first_name', 'sales_rep__user__last_name'
    )
    
    if search_query:
        customers = customers.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_id__icontains=search_query)
        )

    if branch_filter:
        customers = customers.filter(branch_id=branch_filter)

    # Annotate with financial data - OPTIMIZED with date filter on annotation
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

    # Sort and limit to 500 for performance
    customers = customers.order_by(sort_by)[:500]

    # Calculate totals from filtered invoices (efficient)
    base_invoices = Invoice.objects.all()
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
    """Performance report by region/branch - OPTIMIZED"""

    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # CRITICAL FIX: Separate fast queries, combine in Python (avoids massive JOINs)
    
    # Query 1: Invoice stats by branch (uses invoice_branch_date_idx)
    invoice_stats = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('branch_id').annotate(
        total_revenue=Sum('total_with_taxes'),
        total_paid=Sum('amount_paid'),
        total_debt=Sum('amount_due')
    )
    invoice_dict = {item['branch_id']: item for item in invoice_stats}
    
    # Query 2: Order counts by branch (uses purchaseorder_branch_date_idx)
    order_stats = PurchaseOrder.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values('branch_id').annotate(
        total_orders=Count('id')
    )
    order_dict = {item['branch_id']: item['total_orders'] for item in order_stats}
    
    # Query 3: Customer counts by branch (fast, no date filter)
    customer_stats = Customer.objects.values('branch_id').annotate(
        total_customers=Count('id')
    )
    customer_dict = {item['branch_id']: item['total_customers'] for item in customer_stats}
    
    # Query 4: Sales rep counts by branch (fast, no date filter)
    rep_stats = Worker.objects.filter(
        role='Sales Rep',
        is_active=True
    ).values('branch_id').annotate(
        active_sales_reps=Count('id')
    )
    rep_dict = {item['branch_id']: item['active_sales_reps'] for item in rep_stats}
    
    # Query 5: Get branches (fast)
    branches_base = Branch.objects.filter(is_active=True).only('id', 'branch_name')
    
    # Combine all data
    class BranchStats:
        def __init__(self, branch, invoice_data, order_count, customer_count, rep_count):
            self.id = branch.id
            self.branch_name = branch.branch_name
            self.total_revenue = invoice_data.get('total_revenue') or Decimal('0.00')
            self.total_paid = invoice_data.get('total_paid') or Decimal('0.00')
            self.total_debt = invoice_data.get('total_debt') or Decimal('0.00')
            self.total_orders = order_count
            self.total_customers = customer_count
            self.active_sales_reps = rep_count
    
    branches = [
        BranchStats(
            branch,
            invoice_dict.get(branch.id, {}),
            order_dict.get(branch.id, 0),
            customer_dict.get(branch.id, 0),
            rep_dict.get(branch.id, 0)
        )
        for branch in branches_base
    ]
    
    # Sort by revenue
    branches.sort(key=lambda b: b.total_revenue, reverse=True)
    
    # Calculate totals
    totals = {
        'total_revenue': sum(b.total_revenue for b in branches),
        'total_debt': sum(b.total_debt for b in branches),
        'total_orders': sum(b.total_orders for b in branches)
    }

    # Regional comparison chart data
    regional_data = json.dumps([
        {
            'branch_name': b.branch_name,
            'total_revenue': float(b.total_revenue or 0),
            'total_debt': float(b.total_debt or 0),
            'total_orders': b.total_orders or 0
        }
        for b in branches
    ])

    view_context = {
        'branches': branches,
        'totals': totals,
        'regional_data': regional_data,
        'date_from': date_from,
        'date_to': date_to,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/regional_performance.html', context)


@login_required
@manager_required
def sales_agent_performance_report(request):
    """Performance report by sales agent - OPTIMIZED"""

    # Get filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = timezone.now().strftime('%Y-%m-%d')

    # OPTIMIZED: Fetch sales reps with select_related
    sales_reps = Worker.objects.filter(
        role='Sales Rep',
        is_active=True
    ).select_related('user', 'branch')

    if branch_filter:
        sales_reps = sales_reps.filter(branch_id=branch_filter)

    # Annotate with stats from the date range
    sales_reps = sales_reps.annotate(
        total_revenue=Coalesce(
            Sum('invoice_sales_rep_orders__total_with_taxes',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )),
            Decimal('0.00')
        ),
        total_collected=Coalesce(
            Sum('invoice_sales_rep_orders__amount_paid',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )),
            Decimal('0.00')
        ),
        total_outstanding=Coalesce(
            Sum('invoice_sales_rep_orders__amount_due',
                filter=Q(
                    invoice_sales_rep_orders__created_at__date__gte=date_from,
                    invoice_sales_rep_orders__created_at__date__lte=date_to
                )),
            Decimal('0.00')
        ),
        total_orders=Count(
            'invoice_sales_rep_orders',
            filter=Q(
                invoice_sales_rep_orders__created_at__date__gte=date_from,
                invoice_sales_rep_orders__created_at__date__lte=date_to
            )
        ),
        unique_customers=Count(
            'invoice_sales_rep_orders__customer',
            filter=Q(
                invoice_sales_rep_orders__created_at__date__gte=date_from,
                invoice_sales_rep_orders__created_at__date__lte=date_to
            ),
            distinct=True
        )
    ).order_by('-total_revenue')

    # Calculate overall totals
    invoice_query = Invoice.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        sales_rep__role='Sales Rep',
        sales_rep__is_active=True
    )
    
    if branch_filter:
        invoice_query = invoice_query.filter(sales_rep__branch_id=branch_filter)
    
    totals = invoice_query.aggregate(
        total_revenue=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_collected=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_orders=Count('id'),
        total_customers=Count('customer', distinct=True)
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

    # ALL TIME by default - no date filter unless specified
    invoices_qs = Invoice.objects.all()

    if date_from:
        invoices_qs = invoices_qs.filter(created_at__date__gte=date_from)
    if date_to:
        invoices_qs = invoices_qs.filter(created_at__date__lte=date_to)

    # Revenue summary

    revenue_summary = invoices_qs.aggregate(
        total_invoices=Count('id'),
        gross_revenue=Coalesce(Sum('grand_total'), Decimal('0.00')),
        total_with_taxes=Coalesce(Sum('total_with_taxes'), Decimal('0.00')),
        total_collected=Coalesce(Sum('amount_paid'), Decimal('0.00')),
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00'))
    )

    # Payment analysis
    payments = InvoicePayment.objects.all()
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)

    payment_by_method = payments.values('payment_mode').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-total')

    # Cash vs Credit analysis
    cash_credit_qs = PurchaseOrder.objects.all()
    if date_from:
        cash_credit_qs = cash_credit_qs.filter(created_at__date__gte=date_from)
    if date_to:
        cash_credit_qs = cash_credit_qs.filter(created_at__date__lte=date_to)

    cash_credit = cash_credit_qs.values('payment_method').annotate(
        total=Sum('grand_total'),
        count=Count('id')
    )

    # Trend analysis - OPTIMIZED: Limit data points and use only needed fields
    trend_invoices = invoices_qs.only('created_at', 'total_with_taxes', 'amount_paid', 'amount_due')
    
    if view_type == 'daily':
        # Limit to last 90 days for daily view
        trend_start = (timezone.now() - timedelta(days=90)).date()
        trend_data_raw = trend_invoices.filter(
            created_at__date__gte=trend_start
        ).annotate(
            period=TruncDate('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('period')[:90]
    elif view_type == 'weekly':
        # Limit to last 26 weeks
        trend_data_raw = trend_invoices.annotate(
            period=TruncWeek('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('-period')[:26]
    else:  # monthly
        # Limit to last 24 months
        trend_data_raw = trend_invoices.annotate(
            period=TruncMonth('created_at')
        ).values('period').annotate(
            revenue=Sum('total_with_taxes'),
            collected=Sum('amount_paid'),
            outstanding=Sum('amount_due')
        ).order_by('-period')[:24]

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

    # OPTIMIZED: Limit to 200 invoices and use database aggregations
    outstanding_invoices_limited = outstanding_invoices.order_by('created_at')[:200]
    outstanding_invoices_list = list(outstanding_invoices_limited)

    # Add days_outstanding attribute
    for invoice in outstanding_invoices_list:
        invoice.days_outstanding = (today - invoice.created_at.date()).days

    # Summary statistics - use database aggregation, not Python loops
    debt_aggregates = outstanding_invoices.aggregate(
        total_outstanding=Coalesce(Sum('amount_due'), Decimal('0.00')),
        total_invoices=Count('id'),
        avg_outstanding=Coalesce(Avg('amount_due'), Decimal('0.00')),
        oldest_date=Min('created_at')
    )
    
    oldest_debt_days = 0
    if debt_aggregates['oldest_date']:
        oldest_debt_days = (today - debt_aggregates['oldest_date'].date()).days
    
    debt_summary = {
        'total_outstanding': debt_aggregates['total_outstanding'],
        'total_invoices': debt_aggregates['total_invoices'],
        'avg_outstanding': debt_aggregates['avg_outstanding'],
        'oldest_debt_days': oldest_debt_days,
    }

    # OPTIMIZED: Use Customer queryset for template compatibility
    # Build Q filter for branch and age
    debt_filter_q = Q(invoice__amount_due__gt=0)
    if branch_filter:
        debt_filter_q &= Q(invoice__branch_id=branch_filter)
    if age_filter == '0-30':
        debt_filter_q &= Q(invoice__created_at__date__gte=today - timedelta(days=30))
    elif age_filter == '31-60':
        debt_filter_q &= Q(invoice__created_at__date__lt=today - timedelta(days=30), 
                          invoice__created_at__date__gte=today - timedelta(days=60))
    elif age_filter == '61-90':
        debt_filter_q &= Q(invoice__created_at__date__lt=today - timedelta(days=60), 
                          invoice__created_at__date__gte=today - timedelta(days=90))
    elif age_filter == '90+':
        debt_filter_q &= Q(invoice__created_at__date__lt=today - timedelta(days=90))
    
    top_debtors = Customer.objects.annotate(
        total_debt=Coalesce(
            Sum('invoice__amount_due', filter=debt_filter_q),
            Decimal('0.00')
        )
    ).filter(total_debt__gt=0).order_by('-total_debt')[:20]

    # OPTIMIZED: Debt by branch - apply age filter
    debt_by_branch_qs = Invoice.objects.filter(amount_due__gt=0)
    if age_filter == '0-30':
        debt_by_branch_qs = debt_by_branch_qs.filter(created_at__date__gte=today - timedelta(days=30))
    elif age_filter == '31-60':
        debt_by_branch_qs = debt_by_branch_qs.filter(
            created_at__date__lt=today - timedelta(days=30),
            created_at__date__gte=today - timedelta(days=60)
        )
    elif age_filter == '61-90':
        debt_by_branch_qs = debt_by_branch_qs.filter(
            created_at__date__lt=today - timedelta(days=60),
            created_at__date__gte=today - timedelta(days=90)
        )
    elif age_filter == '90+':
        debt_by_branch_qs = debt_by_branch_qs.filter(created_at__date__lt=today - timedelta(days=90))
    
    debt_by_branch = debt_by_branch_qs.values(
        'branch_id',
        'branch__branch_name'
    ).annotate(
        total_debt=Sum('amount_due'),
        invoice_count=Count('id')
    ).order_by('-total_debt')

    # OPTIMIZED: Debt by sales rep - apply branch and age filters
    debt_by_rep_qs = Invoice.objects.filter(
        amount_due__gt=0,
        sales_rep__role='Sales Rep'
    )
    if branch_filter:
        debt_by_rep_qs = debt_by_rep_qs.filter(branch_id=branch_filter)
    if age_filter == '0-30':
        debt_by_rep_qs = debt_by_rep_qs.filter(created_at__date__gte=today - timedelta(days=30))
    elif age_filter == '31-60':
        debt_by_rep_qs = debt_by_rep_qs.filter(
            created_at__date__lt=today - timedelta(days=30),
            created_at__date__gte=today - timedelta(days=60)
        )
    elif age_filter == '61-90':
        debt_by_rep_qs = debt_by_rep_qs.filter(
            created_at__date__lt=today - timedelta(days=60),
            created_at__date__gte=today - timedelta(days=90)
        )
    elif age_filter == '90+':
        debt_by_rep_qs = debt_by_rep_qs.filter(created_at__date__lt=today - timedelta(days=90))
    
    debt_by_rep = debt_by_rep_qs.values(
        'sales_rep_id',
        'sales_rep__employee_id',
        'sales_rep__user__first_name',
        'sales_rep__user__last_name'
    ).annotate(
        total_debt=Sum('amount_due'),
        invoice_count=Count('id')
    ).order_by('-total_debt')[:20]

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


@login_required
@manager_required
def inventory_levels_report(request):
    """Current inventory levels across all branches"""

    # Get filters
    branch_filter = request.GET.get('branch')
    product_filter = request.GET.get('product')
    low_stock_only = request.GET.get('low_stock') == 'true'
    sort_by = request.GET.get('sort', '-total_stock')

    # Base queryset - OPTIMIZED with select_related
    from apps.stock.models import Stock, InventoryTransaction
    from apps.products.models import Product

    stock_qs = Stock.objects.select_related(
        'product__brand_name', 
        'branch', 
        'batch'
    ).all()

    if branch_filter:
        stock_qs = stock_qs.filter(branch_id=branch_filter)
    if product_filter:
        stock_qs = stock_qs.filter(product__product_code__icontains=product_filter)

    # Filter low stock (less than 10 units) - BEFORE annotation for efficiency
    if low_stock_only:
        stock_qs = stock_qs.filter(total_stock__lt=10)

    # Annotate with additional info - INCLUDE GENERIC NAME
    stock_items = stock_qs.annotate(
        product_name=F('product__brand_name__brand_name'),
        generic_name=F('product__brand_name__generic_name'),
        branch_name=F('branch__branch_name'),
        unit_price=F('product__unit_price'),
        stock_value=ExpressionWrapper(
            F('total_stock') * F('product__unit_price'),
            output_field=DecimalField()
        )
    ).values(
        'id', 'product__product_code', 'product_name', 'generic_name', 'branch_name',
        'batch__batch_number', 'batch__expiry_date', 'quantity', 'total_inventory',
        'total_sold', 'total_stock', 'unit_price', 'stock_value'
    )

    # Sort - limit to 1000 for performance
    stock_items = stock_items.order_by(sort_by)[:1000]

    # Calculate totals
    totals = stock_qs.aggregate(
        total_products=Count('id'),
        total_quantity=Coalesce(Sum('total_stock'), 0),
        total_value=Coalesce(
            Sum(ExpressionWrapper(
                F('total_stock') * F('product__unit_price'),
                output_field=DecimalField()
            )),
            Decimal('0.00')
        )
    )

    # Low stock alerts (less than 10 units)
    low_stock_count = stock_qs.filter(total_stock__lt=10).count()

    # Get all branches and products for filters
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')
    products = Product.objects.all().order_by('product_code')[:100]

    view_context = {
        'stock_items': list(stock_items),
        'totals': totals,
        'low_stock_count': low_stock_count,
        'branches': branches,
        'products': products,
        'selected_branch': branch_filter,
        'product_filter': product_filter,
        'low_stock_only': low_stock_only,
        'sort_by': sort_by,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/inventory_levels.html', context)


@login_required
@manager_required
def product_performance_report(request):
    """Product sales and revenue performance"""

    # Get filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')
    sort_by = request.GET.get('sort', '-total_revenue')

    # Base queryset for invoice items
    from apps.orders.models import InvoiceOrderItem

    items_qs = InvoiceOrderItem.objects.select_related('stock__product__brand_name', 'invoice_order').all()

    # Apply filters (FIXED: use invoice_order, not invoice)
    if date_from:
        items_qs = items_qs.filter(invoice_order__created_at__date__gte=date_from)
    if date_to:
        items_qs = items_qs.filter(invoice_order__created_at__date__lte=date_to)
    if branch_filter:
        items_qs = items_qs.filter(invoice_order__branch_id=branch_filter)

    # Group by product and calculate metrics - INCLUDE GENERIC NAME & BRAND NAME
    product_sales = items_qs.values(
        'stock__product__product_code',
        'stock__product__brand_name__brand_name',
        'stock__product__brand_name__generic_name',
        'stock__product__unit_price'
    ).annotate(
        total_quantity_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price')),
        number_of_orders=Count('invoice_order', distinct=True)
    ).order_by(sort_by)

    # Convert to list for JSON serialization
    product_sales_list = []
    for item in product_sales:
        product_sales_list.append({
            'product_code': item['stock__product__product_code'],
            'product_name': item['stock__product__brand_name__brand_name'] or 'N/A',
            'generic_name': item['stock__product__brand_name__generic_name'] or 'N/A',
            'unit_price': float(item['stock__product__unit_price'] or 0),
            'quantity_sold': int(item['total_quantity_sold'] or 0),
            'revenue': float(item['total_revenue'] or 0),
            'orders': int(item['number_of_orders'] or 0)
        })

    # Calculate totals
    totals = items_qs.aggregate(
        total_products_sold=Count('stock__product', distinct=True),
        total_quantity=Coalesce(Sum('quantity'), 0),
        total_revenue=Coalesce(Sum(F('quantity') * F('price')), Decimal('0.00'))
    )

    # Top 10 products chart data (by revenue) - INCLUDE GENERIC NAME
    top_products = product_sales[:10]
    top_products_data = [
        {
            'product': item['stock__product__product_code'],
            'generic_name': item['stock__product__brand_name__generic_name'] or 'N/A',
            'revenue': float(item['total_revenue'] or 0)
        }
        for item in top_products
    ]

    # Top 10 products by quantity sold - INCLUDE GENERIC NAME
    top_products_by_quantity = sorted(
        product_sales_list,
        key=lambda x: x['quantity_sold'],
        reverse=True
    )[:10]
    top_products_quantity_data = [
        {
            'product': item['product_code'],
            'generic_name': item['generic_name'],
            'quantity': item['quantity_sold']
        }
        for item in top_products_by_quantity
    ]

    # Get all branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'product_sales': product_sales_list,
        'totals': totals,
        'top_products_data': json.dumps(top_products_data),
        'top_products_quantity_data': json.dumps(top_products_quantity_data),
        'branches': branches,
        'date_from': date_from,
        'date_to': date_to,
        'selected_branch': branch_filter,
        'sort_by': sort_by,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/product_performance.html', context)


@login_required
@manager_required
def stock_movement_report(request):
    """Stock transfers and movements between branches"""

    # Get filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    branch_filter = request.GET.get('branch')
    movement_type = request.GET.get('movement_type')  # 'in' or 'out'

    # Base queryset
    from apps.stock_request.models import StockTransfer, StockTransferItem

    # Get stock transfers with details
    transfers_qs = StockTransfer.objects.select_related(
        'source_branch', 'destination_branch', 'transferred_by'
    ).prefetch_related('items__product').all()

    if date_from:
        transfers_qs = transfers_qs.filter(date_transferred__date__gte=date_from)
    if date_to:
        transfers_qs = transfers_qs.filter(date_transferred__date__lte=date_to)
    if branch_filter:
        transfers_qs = transfers_qs.filter(
            Q(source_branch_id=branch_filter) | Q(destination_branch_id=branch_filter)
        )
    if movement_type == 'out':
        transfers_qs = transfers_qs.filter(source_branch_id=branch_filter)
    elif movement_type == 'in':
        transfers_qs = transfers_qs.filter(destination_branch_id=branch_filter)

    transfers = transfers_qs.order_by('-date_transferred')[:50]

    # Calculate statistics
    total_transfers = transfers_qs.count()
    pending_transfers = transfers_qs.filter(status='Pending').count()
    completed_transfers = transfers_qs.filter(status='Received').count()

    # Get all branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'transfers': transfers,
        'total_transfers': total_transfers,
        'pending_transfers': pending_transfers,
        'completed_transfers': completed_transfers,
        'branches': branches,
        'date_from': date_from,
        'date_to': date_to,
        'selected_branch': branch_filter,
        'movement_type': movement_type,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/stock_movement.html', context)


@login_required
@manager_required
def inventory_valuation_report(request):
    """Total inventory value across branches"""

    # Get filters
    branch_filter = request.GET.get('branch')

    # Base queryset
    from apps.stock.models import Stock

    stock_qs = Stock.objects.select_related('product', 'branch', 'batch').all()

    if branch_filter:
        stock_qs = stock_qs.filter(branch_id=branch_filter)

    # Annotate each stock item with its value first
    stock_with_value = stock_qs.annotate(
        stock_value=ExpressionWrapper(
            F('total_stock') * F('product__unit_price'),
            output_field=DecimalField()
        )
    )

    # Calculate valuation by branch
    valuation_by_branch = stock_with_value.values('branch__branch_name').annotate(
        total_stock=Sum('total_stock'),
        total_value=Sum('stock_value'),
        products_count=Count('id')
    ).order_by('-total_value')

    # Convert to JSON-safe format for charts
    branch_valuation_data = [
        {
            'branch': item['branch__branch_name'],
            'value': float(item['total_value'] or 0)
        }
        for item in valuation_by_branch
    ]

    # Top 20 products by value
    top_products_by_value = stock_with_value.values(
        'product__product_code',
        'product__brand_name__brand_name',
        'product__unit_price'
    ).annotate(
        total_stock=Sum('total_stock'),
        total_value=Sum('stock_value')
    ).order_by('-total_value')[:20]

    # Calculate overall totals
    overall_totals = stock_with_value.aggregate(
        total_inventory_value=Coalesce(Sum('stock_value'), Decimal('0.00')),
        total_units=Coalesce(Sum('total_stock'), 0),
        unique_products=Count('product', distinct=True)
    )

    # Get all branches for filter
    branches = Branch.objects.filter(is_active=True).order_by('branch_name')

    view_context = {
        'valuation_by_branch': valuation_by_branch,
        'top_products_by_value': top_products_by_value,
        'overall_totals': overall_totals,
        'branch_valuation_data': json.dumps(branch_valuation_data),
        'branches': branches,
        'selected_branch': branch_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/inventory_valuation.html', context)


# Export functionality
@login_required
@manager_required
def export_report(request, report_type):
    """Export report to Excel or PDF"""
    export_format = request.GET.get('format', 'excel')

    try:
        if export_format == 'excel':
            return export_to_excel(request, report_type)
        elif export_format == 'pdf':
            return export_to_pdf(request, report_type)
        else:
            messages.error(request, f"Unsupported export format: {export_format}")
            return redirect('reports_dashboard')
    except Exception as e:
        messages.error(request, f"Error exporting report: {str(e)}")
        return redirect('reports_dashboard')


def export_to_excel(request, report_type):
    """Export report data to Excel"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from datetime import datetime

    # Create workbook
    wb = Workbook()
    ws = wb.active

    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)

    if report_type == 'client-financial':
        ws.title = "Client Financial Report"

        # Get data
        customers = Customer.objects.annotate(
            total_revenue=Coalesce(Sum('invoice__total_with_taxes'), Decimal('0.00')),
            total_paid=Coalesce(Sum('invoice__amount_paid'), Decimal('0.00')),
            total_debt=Coalesce(Sum('invoice__amount_due'), Decimal('0.00')),
        ).order_by('-total_debt')

        # Headers
        headers = ['Customer ID', 'Customer Name', 'Total Revenue', 'Total Paid', 'Outstanding Debt']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Data
        for row_num, customer in enumerate(customers, 2):
            ws.cell(row=row_num, column=1, value=customer.customer_id)
            ws.cell(row=row_num, column=2, value=customer.customer_name)
            ws.cell(row=row_num, column=3, value=float(customer.total_revenue))
            ws.cell(row=row_num, column=4, value=float(customer.total_paid))
            ws.cell(row=row_num, column=5, value=float(customer.total_debt))

    elif report_type == 'inventory-levels':
        ws.title = "Inventory Levels"

        # Get data
        from apps.stock.models import Stock
        stock_items = Stock.objects.select_related('product', 'branch', 'batch').all()

        # Headers
        headers = ['Product Code', 'Product Name', 'Branch', 'Batch', 'Total Stock', 'Total Sold', 'Unit Price', 'Stock Value']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Data
        for row_num, item in enumerate(stock_items, 2):
            ws.cell(row=row_num, column=1, value=item.product.product_code)
            ws.cell(row=row_num, column=2, value=item.product.brand_name.brand_name if item.product.brand_name else 'N/A')
            ws.cell(row=row_num, column=3, value=item.branch.branch_name)
            ws.cell(row=row_num, column=4, value=item.batch.batch_number if item.batch else 'N/A')
            ws.cell(row=row_num, column=5, value=item.total_stock)
            ws.cell(row=row_num, column=6, value=item.total_sold)
            ws.cell(row=row_num, column=7, value=float(item.product.unit_price))
            ws.cell(row=row_num, column=8, value=float(item.total_stock * item.product.unit_price))

    elif report_type == 'product-performance':
        ws.title = "Product Performance"

        # Get data
        from apps.orders.models import InvoiceOrderItem
        product_sales = InvoiceOrderItem.objects.values(
            'stock__product__product_code',
            'stock__product__brand_name__brand_name',
            'stock__product__unit_price'
        ).annotate(
            total_quantity_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price')),
            number_of_orders=Count('invoice_order', distinct=True)
        ).order_by('-total_revenue')[:100]

        # Headers
        headers = ['Product Code', 'Product Name', 'Unit Price', 'Quantity Sold', 'Total Revenue', 'Number of Orders']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Data
        for row_num, item in enumerate(product_sales, 2):
            ws.cell(row=row_num, column=1, value=item['stock__product__product_code'])
            ws.cell(row=row_num, column=2, value=item['stock__product__brand_name__brand_name'] or 'N/A')
            ws.cell(row=row_num, column=3, value=float(item['stock__product__unit_price'] or 0))
            ws.cell(row=row_num, column=4, value=item['total_quantity_sold'])
            ws.cell(row=row_num, column=5, value=float(item['total_revenue'] or 0))
            ws.cell(row=row_num, column=6, value=item['number_of_orders'])

    else:
        # Generic export with summary
        ws.title = "Report"
        ws.cell(row=1, column=1, value="Report Type")
        ws.cell(row=1, column=2, value=report_type)
        ws.cell(row=2, column=1, value="Generated Date")
        ws.cell(row=2, column=2, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


def export_to_pdf(request, report_type):
    """Export report data to PDF"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from django.http import HttpResponse
    from datetime import datetime
    from io import BytesIO

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1  # Center
    )

    # Add title
    title_text = report_type.replace('-', ' ').title() + " Report"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # Prepare data based on report type
    if report_type == 'client-financial':
        customers = Customer.objects.annotate(
            total_revenue=Coalesce(Sum('invoice__total_with_taxes'), Decimal('0.00')),
            total_debt=Coalesce(Sum('invoice__amount_due'), Decimal('0.00')),
        ).order_by('-total_debt')[:50]

        data = [['Customer ID', 'Customer Name', 'Revenue', 'Debt']]
        for customer in customers:
            data.append([
                customer.customer_id,
                customer.customer_name[:30],  # Truncate long names
                f"{float(customer.total_revenue):,.0f}",
                f"{float(customer.total_debt):,.0f}"
            ])

    elif report_type == 'inventory-levels':
        from apps.stock.models import Stock
        stock_items = Stock.objects.select_related('product', 'branch')[:50]

        data = [['Product Code', 'Product', 'Branch', 'Stock', 'Value']]
        for item in stock_items:
            data.append([
                item.product.product_code,
                (item.product.brand_name.brand_name if item.product.brand_name else 'N/A')[:20],
                item.branch.branch_name[:15],
                str(item.total_stock),
                f"{float(item.total_stock * item.product.unit_price):,.0f}"
            ])

    else:
        data = [['Report Type', report_type], ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)

    # Prepare response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
