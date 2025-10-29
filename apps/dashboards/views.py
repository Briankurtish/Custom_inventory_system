from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.workers.models import Worker, RolePrivilege
from apps.stock_request.models import StockRequest
from django.utils.translation import activate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notice
from .forms import NoticeForm
from apps.orders.models import PurchaseOrder, Invoice
from apps.stock.models import Stock
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import json


class DashboardsView(LoginRequiredMixin, TemplateView):
    # Default fallback template
    template_name = "dashboard_analytics.html"

    def get_template_names(self):
        """
        Dynamically select the template based on the worker's role.
        """
        if self.request.user.is_authenticated:
            try:
                # Retrieve the worker's role
                worker = self.request.user.worker_profile
                role_template_map = {
                    'Director': 'dashboard_analytics.html',
                    'Pharmacist': 'dashboard_pharmacist.html',
                    'Marketing Director': 'dashboard_md.html',
                    'Central Stock Manager': 'dashboard_cstm.html',
                    'Stock Manager': 'dashboard_stkm.html',
                    'Stock Keeper': 'dashboard_stk-keeper.html',
                    'Accountant': 'dashboard_acc.html',
                    'Cashier': 'dashboard_cash.html',
                    'Secretary': 'dashboard_sec.html',
                    'Sales Rep': 'dashboard_cstm.html',
                    'Driver': 'dashboard_driver.html',
                    'Other': 'dashboard_analytics.html',
                }
                # Return the specific template for the role or the default
                return [role_template_map.get(worker.role, self.template_name)]
            except Worker.DoesNotExist:
                # If no worker profile exists, fallback to default template
                return [self.template_name]
        return super().get_template_names()

    def get_sales_data(self):
        """
        Get monthly sales data for the last 12 months.
        Returns a list of sales counts per month.
        """
        # Get the current date and calculate 12 months ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Query orders grouped by month
        monthly_sales = (
            PurchaseOrder.objects
            .filter(created_at__gte=start_date, created_at__lte=end_date)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # Create a dictionary with all 12 months initialized to 0
        sales_dict = {}
        for i in range(12):
            month_date = end_date - timedelta(days=30 * (11 - i))
            month_key = month_date.strftime('%Y-%m')
            sales_dict[month_key] = 0

        # Fill in the actual sales data
        for sale in monthly_sales:
            month_key = sale['month'].strftime('%Y-%m')
            if month_key in sales_dict:
                sales_dict[month_key] = sale['count']

        # Return the values as a list
        return list(sales_dict.values())

    def get_inventory_data(self):
        """
        Get inventory data categorized as In Stock, Low Stock, and Out of Stock
        for the last 12 months.
        """
        # Get the current date and calculate 12 months ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Define stock levels thresholds
        LOW_STOCK_THRESHOLD = 20  # Products with quantity <= 20

        # Get stock data grouped by month
        monthly_stock = (
            Stock.objects
            .filter(date_added__gte=start_date, date_added__lte=end_date)
            .annotate(month=TruncMonth('date_added'))
            .values('month')
            .annotate(
                in_stock=Count('id', filter=Q(quantity__gt=LOW_STOCK_THRESHOLD)),
                low_stock=Count('id', filter=Q(quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD)),
                out_of_stock=Count('id', filter=Q(quantity=0))
            )
            .order_by('month')
        )

        # Create dictionaries with all 12 months initialized to 0
        in_stock_dict = {}
        low_stock_dict = {}
        out_of_stock_dict = {}

        for i in range(12):
            month_date = end_date - timedelta(days=30 * (11 - i))
            month_key = month_date.strftime('%Y-%m')
            in_stock_dict[month_key] = 0
            low_stock_dict[month_key] = 0
            out_of_stock_dict[month_key] = 0

        # Fill in the actual inventory data
        for stock in monthly_stock:
            month_key = stock['month'].strftime('%Y-%m')
            if month_key in in_stock_dict:
                in_stock_dict[month_key] = stock['in_stock']
                low_stock_dict[month_key] = stock['low_stock']
                out_of_stock_dict[month_key] = stock['out_of_stock']

        # Return as separate lists
        return {
            'in_stock': list(in_stock_dict.values()),
            'low_stock': list(low_stock_dict.values()),
            'out_of_stock': list(out_of_stock_dict.values())
        }

    def get_financial_data(self):
        """
        Get financial analytics data from invoices.
        Returns dict with various financial metrics.
        """
        from decimal import Decimal

        # Get all invoices
        invoices = Invoice.objects.all()

        # Calculate total revenue (amount paid)
        total_paid = invoices.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')

        # Calculate pending payments (amount due)
        total_pending = invoices.aggregate(
            total=Sum('amount_due')
        )['total'] or Decimal('0.00')

        # Calculate total invoice value (with taxes)
        total_revenue = invoices.aggregate(
            total=Sum('total_with_taxes')
        )['total'] or Decimal('0.00')

        # Count invoices by status
        unpaid_count = invoices.filter(status='Unpaid').count()
        payment_ongoing_count = invoices.filter(status='Payment Ongoing').count()
        completed_count = invoices.filter(status='Payment Completed').count()

        # Calculate payment completion percentage
        total_invoices = invoices.count()
        completion_rate = (completed_count / total_invoices * 100) if total_invoices > 0 else 0

        return {
            'total_paid': float(total_paid),
            'total_pending': float(total_pending),
            'total_revenue': float(total_revenue),
            'unpaid_count': unpaid_count,
            'payment_ongoing_count': payment_ongoing_count,
            'completed_count': completed_count,
            'completion_rate': round(completion_rate, 1),
            'total_invoices': total_invoices
        }

    def get_context_data(self, **kwargs):
        """
        Add additional context data if needed.
        """
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['role'] = getattr(self.request.user.worker_profile, 'role', 'Unknown')

        # Add the count of pending stock requests
        context['pending_request_count'] = StockRequest.objects.filter(status='Pending').count()
        context['accepted_request_count'] = StockRequest.objects.filter(status='Accepted').count()


        # Add the notices to the context
        context['notices'] = Notice.objects.filter(is_active=True).order_by("-created_at")

        # Check if the user is logging in for the first time (last_login is None)
        show_password_modal = self.request.user.last_login is None
        if show_password_modal:
            # Refresh user object to ensure last_login is set
            self.request.user.refresh_from_db()

        # Add the flag to show the modal
        context['show_password_modal'] = show_password_modal

        # Add chart data
        context['sales_data'] = json.dumps(self.get_sales_data())
        context['inventory_data'] = json.dumps(self.get_inventory_data())

        # Add financial data
        financial_data = self.get_financial_data()
        context.update(financial_data)

        return context


@login_required
def notice_board(request):
    notices = Notice.objects.filter(is_active=True).order_by("-created_at")
    form = NoticeForm()

    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user.worker_profile  # Assuming worker_profile is linked
            notice.save()
            messages.success(request, "Notice posted successfully!")
            return redirect("notice_board")

    context = TemplateLayout.init(
        request,
        {"notices": notices, "form": form}
    )

    return render(request, "new_notice.html", context)




@login_required
def delete_notice(request, pk):
    try:
        notice = Notice.objects.get(pk=pk)
        notice.delete()
        messages.success(request, "Notice deleted successfully!")
    except Notice.DoesNotExist:
        messages.error(request, "Notice not found.")
    return redirect("notice_board")
