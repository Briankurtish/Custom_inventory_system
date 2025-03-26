from django.views.generic import TemplateView
from apps.workers.models import Worker
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Customer, CustomerAuditLog
from .forms import CustomerForm
from apps.branches.models import Branch
from django.contrib.auth.decorators import login_required
from apps.oldinvoice.models import OldInvoiceOrder
from django.core.paginator import Paginator
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

@login_required
def ManageCustomerView(request):
    # Get all branches for the filter dropdown
    branches = Branch.objects.all()

    # Get the worker profile
    worker = request.user.worker_profile

    # Determine if the user is a superuser
    is_superuser = request.user.is_superuser

    # Get filters from the request
    branch_filter = request.GET.get('branch_filter')
    search_query = request.GET.get('search_query', '').strip()

    # Filter customers based on the user's privileges and search query
    if is_superuser:
        # Superuser sees all customers
        customers = Customer.objects.all()
    else:
        # Regular users see customers only from their branch
        worker_branch = worker.branch
        if branch_filter:
            customers = Customer.objects.filter(branch_id=branch_filter, branch=worker_branch)
        else:
            customers = Customer.objects.filter(branch=worker_branch)

    # Apply the search filter if a search query is provided
    if search_query:
        customers = customers.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_id__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(telephone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(agreement_number__icontains=search_query) |
            Q(tax_payer_number__icontains=search_query)
        )

    # Order the customers by name
    customers = customers.order_by('customer_name')

    # Get worker privileges
    worker_privileges = worker.privileges.values_list('name', flat=True)

    # Paginate the customers
    paginator = Paginator(customers, 100)
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_customers = paginator.get_page(page_number)

    # Calculate the offset based on the current page and number of items per page
    offset = (paginated_customers.number - 1) * paginator.per_page

    # Context for the template
    view_context = {
        "customers": paginated_customers,
        "branches": branches,
        "branch_filter": branch_filter,  # Pass the selected branch filter back to the template
        "search_query": search_query,  # Pass the search query back to the template
        "worker_privileges": worker_privileges,
        "offset": offset,  # Pass the offset to the template
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'customers.html', context)


@login_required
def CustomerAuditLogView(request):
    logs = CustomerAuditLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 100)  # Paginate logs with 10 logs per page
    page_number = request.GET.get("page")  # Get the current page number from the request
    paginated_logs = paginator.get_page(page_number)  # Get the page object
    offset = (paginated_logs.number - 1) * paginator.per_page
    # Create a context dictionary for the view
    view_context = {
        "logs": paginated_logs,
        "offset": offset,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "customer_logs.html", context)


@login_required
def customer_view(request, pk=None):
    """
    Handles both adding and updating a customer.
    If pk is None, it creates a new customer; otherwise, it updates the existing customer.
    """

    if pk:
        customer = get_object_or_404(Customer, pk=pk)
        form = CustomerForm(request.POST or None, request.FILES or None, instance=customer)
        action = "updated"
    else:
        customer = None
        form = CustomerForm(request.POST or None, request.FILES or None)
        action = "created"

    if request.method == "POST":
        if form.is_valid():
            # Check for duplicates with the same name and postal code
            duplicate_check = Customer.objects.filter(
                customer_name=form.cleaned_data['customer_name'],
                postal_code=form.cleaned_data.get('postal_code')
            )
            if pk:
                duplicate_check = duplicate_check.exclude(pk=pk)

            if duplicate_check.exists():
                messages.error(request, _("A customer with the same name and postal code already exists."))
            else:
                customer = form.save(commit=False)
                if not pk:
                    # Set the creator for new customers
                    try:
                        customer.created_by = request.user.worker_profile
                    except AttributeError:
                        messages.error(request, _("Worker profile not found for the current user."))
                        return redirect('customers')

                customer.save()

                # Log the action
                try:
                    worker = request.user.worker_profile
                except AttributeError:
                    worker = None

                log_details = f"Customer {action}d by {'admin' if worker is None else worker}."
                CustomerAuditLog.objects.create(
                    user=worker,
                    customer_name=customer.customer_name,
                    action=action,
                    details=log_details
                )

                # Set success message and redirect
                messages.success(request, _(f"Customer {action} successfully."))
                return redirect('customers')

        else:
            messages.error(request, _("Please correct the errors below."))

    # Fetch all customers for display
    customers = Customer.objects.all().order_by('-created_at')

    # Prepare context for rendering
    view_context = {
        "form": form,
        "customers": customers,
        "is_editing": bool(pk),
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

        # Handle the audit log before deletion
        if request.user.username == "admin":
            # Special case for admin account (no associated Worker)
            CustomerAuditLog.objects.create(
                user=None,  # No associated Worker
                customer_name=customer.customer_name,  # Store branch name directly
                action="delete",
                details=f"Custonmer '{customer.customer_name}' deleted by admin."
            )
        else:
            # Try to retrieve the Worker instance
            try:
                worker = request.user.worker_profile
                CustomerAuditLog.objects.create(
                    user=worker,
                    customer_name=customer.customer_name,  # Store branch name directly
                    action="delete",
                    details=f"Customer '{customer.customer_name}' deleted by {worker}."
                )
            except Worker.DoesNotExist:
                messages.error(request, "Worker profile not found for the current user.")
                return redirect("customers")  # Handle error appropriately

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
