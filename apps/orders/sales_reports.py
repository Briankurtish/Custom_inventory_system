from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from apps.orders.models import PurchaseOrder, PurchaseOrderItem
from apps.customers.models import Customer
from apps.branches.models import Branch
from apps.workers.models import Worker
from web_project import TemplateLayout
from django.core.paginator import Paginator


@login_required
def sales_report_by_customer(request):
    """
    Comprehensive sales report with filtering by customer, date range, and product
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "You don't have permission to access this report. Contact your administrator.")
        return redirect('index')

    # Get filter parameters
    customer_id = request.GET.get('customer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    branch_id = request.GET.get('branch')
    product_search = request.GET.get('product_search', '')

    # Initialize date variables
    start = None
    end = None

    # Base queryset
    orders = PurchaseOrder.objects.all().select_related('customer', 'branch', 'created_by')

    # Apply filters
    if customer_id:
        orders = orders.filter(customer_id=customer_id)

    if start_date and start_date != 'None':
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            orders = orders.filter(created_at__gte=start)
        except ValueError:
            pass

    if end_date and end_date != 'None':
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            orders = orders.filter(created_at__lte=end)
        except ValueError:
            pass

    if branch_id:
        orders = orders.filter(branch_id=branch_id)

    # Calculate totals
    summary_stats = orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('grand_total'),
        total_items_sold=Sum('items__quantity')
    )

    # Get customer-wise breakdown
    customer_breakdown = (
        PurchaseOrder.objects
        .values('customer__customer_name', 'customer__id')
        .annotate(
            total_orders=Count('id'),
            total_quantity=Sum('items__quantity'),
            total_revenue=Sum('grand_total')
        )
        .order_by('-total_revenue')
    )

    # Apply same filters to customer breakdown
    if start:
        customer_breakdown = customer_breakdown.filter(created_at__gte=start)

    if end:
        customer_breakdown = customer_breakdown.filter(created_at__lte=end)

    if branch_id:
        customer_breakdown = customer_breakdown.filter(branch_id=branch_id)

    # Product-level details if product search is provided
    product_details = None
    if product_search:
        product_details = (
            PurchaseOrderItem.objects
            .filter(
                Q(stock__product__product_code__icontains=product_search) |
                Q(stock__product__generic_name_dosage__generic_name__icontains=product_search) |
                Q(stock__product__brand_name__brand_name__icontains=product_search)
            )
            .select_related('purchase_order', 'purchase_order__customer', 'stock', 'stock__product')
            .order_by('-purchase_order__created_at')
        )

        # Apply filters to product details
        if customer_id:
            product_details = product_details.filter(purchase_order__customer_id=customer_id)
        if start:
            product_details = product_details.filter(purchase_order__created_at__gte=start)
        if end:
            product_details = product_details.filter(purchase_order__created_at__lte=end)
        if branch_id:
            product_details = product_details.filter(purchase_order__branch_id=branch_id)

    # Pagination for orders
    paginator = Paginator(orders.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    paginated_orders = paginator.get_page(page_number)

    view_context = {
        'orders': paginated_orders,
        'customers': Customer.objects.all().order_by('customer_name'),
        'branches': Branch.objects.filter(is_active=True),
        'summary_stats': summary_stats,
        'customer_breakdown': customer_breakdown[:20],  # Top 20 customers
        'product_details': product_details,
        'selected_customer': customer_id,
        'start_date': start_date,
        'end_date': end_date,
        'branch_id': branch_id,
        'product_search': product_search,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/sales_by_customer.html', context)


@login_required
def employee_treatment_report(request):
    """
    Report for tracking employee personal treatment (sickness) orders
    to prevent abuse and fraud
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "You don't have permission to access this report. Contact your administrator.")
        return redirect('index')

    from apps.orders.models import Sickness, SicknessItem

    # Get filter parameters
    employee_id = request.GET.get('employee')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    branch_id = request.GET.get('branch')
    month = request.GET.get('month')
    year = request.GET.get('year', timezone.now().year)

    # Base queryset
    sickness_orders = Sickness.objects.all().select_related('employee', 'branch', 'created_by')

    # Initialize date variables
    start = None
    end = None

    # Apply filters
    if employee_id:
        sickness_orders = sickness_orders.filter(employee_id=employee_id)

    if start_date and start_date != 'None':
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            sickness_orders = sickness_orders.filter(created_at__gte=start)
        except ValueError:
            pass

    if end_date and end_date != 'None':
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            sickness_orders = sickness_orders.filter(created_at__lte=end)
        except ValueError:
            pass

    if branch_id:
        sickness_orders = sickness_orders.filter(branch_id=branch_id)

    if month:
        sickness_orders = sickness_orders.filter(created_at__month=month, created_at__year=year)

    # Calculate summary statistics
    summary_stats = sickness_orders.aggregate(
        total_orders=Count('id'),
        total_items=Sum('sickness_items__quantity'),
        total_cost=Count('sickness_items')  # Count items as cost placeholder since no grand_total field
    )

    # Employee-wise breakdown
    employee_breakdown = (
        Sickness.objects
        .values('employee__user__first_name', 'employee__user__last_name', 'employee__id')
        .annotate(
            total_orders=Count('id'),
            total_quantity=Sum('sickness_items__quantity'),
            total_cost=Count('sickness_items')  # Count items as cost placeholder
        )
        .order_by('-total_cost')
    )

    # Apply same filters to employee breakdown
    if start:
        employee_breakdown = employee_breakdown.filter(created_at__gte=start)
    if end:
        employee_breakdown = employee_breakdown.filter(created_at__lte=end)
    if branch_id:
        employee_breakdown = employee_breakdown.filter(branch_id=branch_id)
    if month:
        employee_breakdown = employee_breakdown.filter(created_at__month=month, created_at__year=year)

    # Detailed items breakdown by product
    product_breakdown = (
        SicknessItem.objects
        .values(
            'stock__product__product_code',
            'stock__product__generic_name_dosage__generic_name',
            'stock__product__brand_name__brand_name'
        )
        .annotate(
            total_quantity=Sum('quantity'),
            times_ordered=Count('id')
        )
        .order_by('-total_quantity')
    )

    # Apply filters
    if employee_id:
        product_breakdown = product_breakdown.filter(sickness_order__employee_id=employee_id)
    if start:
        product_breakdown = product_breakdown.filter(sickness_order__created_at__gte=start)
    if end:
        product_breakdown = product_breakdown.filter(sickness_order__created_at__lte=end)
    if branch_id:
        product_breakdown = product_breakdown.filter(sickness_order__branch_id=branch_id)
    if month:
        product_breakdown = product_breakdown.filter(
            sickness_order__created_at__month=month,
            sickness_order__created_at__year=year
        )

    # Flag potential abuse (e.g., same employee ordering more than threshold in a month)
    abuse_alerts = []
    for emp in employee_breakdown:
        total_qty = emp['total_quantity'] or 0
        if emp['total_orders'] > 5 or total_qty > 20:  # Threshold
            abuse_alerts.append({
                'employee': f"{emp['employee__user__first_name']} {emp['employee__user__last_name']}",
                'orders': emp['total_orders'],
                'quantity': total_qty,
                'cost': emp['total_cost'] or 0,
                'alert_level': 'warning' if emp['total_orders'] <= 8 else 'danger'
            })

    # Pagination
    paginator = Paginator(sickness_orders.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    paginated_orders = paginator.get_page(page_number)

    view_context = {
        'sickness_orders': paginated_orders,
        'employees': Worker.objects.all().select_related('user'),
        'branches': Branch.objects.filter(is_active=True),
        'summary_stats': summary_stats,
        'employee_breakdown': employee_breakdown,
        'product_breakdown': product_breakdown[:30],  # Top 30 products
        'abuse_alerts': abuse_alerts,
        'selected_employee': employee_id,
        'start_date': start_date,
        'end_date': end_date,
        'branch_id': branch_id,
        'selected_month': month,
        'year': year,
        'months': [
            {'id': 1, 'name': 'January'}, {'id': 2, 'name': 'February'},
            {'id': 3, 'name': 'March'}, {'id': 4, 'name': 'April'},
            {'id': 5, 'name': 'May'}, {'id': 6, 'name': 'June'},
            {'id': 7, 'name': 'July'}, {'id': 8, 'name': 'August'},
            {'id': 9, 'name': 'September'}, {'id': 10, 'name': 'October'},
            {'id': 11, 'name': 'November'}, {'id': 12, 'name': 'December'},
        ],
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'reports/employee_treatment_report.html', context)
