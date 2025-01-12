from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Customer
from .forms import CustomerForm
from django.contrib.auth.decorators import login_required
from apps.oldinvoice.models import OldInvoiceOrder
from django.core.paginator import Paginator
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.utils.translation import gettext_lazy as _
from django.contrib import messages


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

@login_required
def ManageCustomerView(request):
    customers = Customer.objects.all()
    worker = request.user.worker_profile
    worker_privileges = worker.privileges.values_list('name', flat=True)

    paginator = Paginator(customers, 10) 
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_customers = paginator.get_page(page_number)
    
    # Create a new context dictionary for this view 
    view_context = {
        "customers": paginated_customers,
        'worker_privileges': worker_privileges,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'customers.html', context)

@login_required
def customer_view(request, pk=None):
    """
    Handles both adding and updating a customer.
    If pk is None, it creates a new customer; otherwise, it updates the existing customer.
    """
    customer = get_object_or_404(Customer, pk=pk) if pk else None
    form = CustomerForm(request.POST or None, request.FILES or None, instance=customer)
    
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Customer created successfully"))
        return redirect('customers')  # Redirect to customer list or any desired page

    customers = Customer.objects.all()  # Fetch all customers for display

    view_context = {
        "form": form,
        "customers": customers,
        "is_editing": bool(pk),  # Determine if we're editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addCustomer.html', context)

@login_required
def delete_customer_view(request, pk):
    """
    Handles deleting a crypto wallet.
    """
    customer = get_object_or_404(Customer, id=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, _("Customer record deleted successfully"))
        return redirect("customers")

    view_context = {
        "customer": customer,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteCustomer.html', context)


@login_required
def get_credit_report(request, customer_id):
    """
    View to retrieve and display a specific customer's credit history from OldInvoiceOrder.
    """
    # Get the customer object
    customer = get_object_or_404(Customer, id=customer_id)

    # Fetch all orders for the customer where payment is credit
    credit_orders = OldInvoiceOrder.objects.filter(
        customer=customer, payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid"),  # Renamed annotation
    ).order_by("-created_at")

    # Current invoice: the latest one
    current_invoice = credit_orders.first()

    # Calculate total due
    total_due = credit_orders.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0

    view_context = {
        "customer": customer,
        "credit_orders": credit_orders,
        "total_due": total_due,
        "current_invoice": current_invoice,  # Pass the current invoice
    }

    # Use TemplateLayout for consistent UI
    context = TemplateLayout.init(request, view_context)
    return render(request, "customerCreditReport.html", context)