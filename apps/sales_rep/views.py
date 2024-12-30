from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import SalesAgent
from .forms import SalesAgentForm
from apps.branches.models import Branch
from apps.workers.models import Worker
from django.contrib.auth.decorators import login_required
from apps.oldinvoice.models import OldInvoiceOrder
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageSalesRepView(request):
    # Filter workers whose role is "Sales Rep" from the Worker table
    salesRep = Worker.objects.filter(role__iexact="Sales Rep")  # Case-insensitive match for "Sales Rep"
    worker = request.user.worker_profile
    worker_privileges = worker.privileges.values_list('name', flat=True)
    
    
    paginator = Paginator(salesRep, 10) 
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_slaes_rep = paginator.get_page(page_number)
    
    # Create a new context dictionary for this view 
    view_context = {
        "salesRep": paginated_slaes_rep,
        'worker_privileges': worker_privileges,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'sales-rep.html', context)



def add_salesRep_view(request, pk=None):
    salesRep = SalesAgent.objects.all() 
    
    if pk:
        salesRep = get_object_or_404(SalesAgent, pk=pk)  # Fetch the product for editing
        form = SalesAgentForm(request.POST or None, instance=salesRep)  # Bind the form to the existing product
    else:
        salesRep = None
        form = SalesAgentForm(request.POST or None)  # Empty form for creating a new product

    # Handle the POST request (form submission)
    if request.method == "POST":
        if form.is_valid():
            form.save()  # Save the product (create or update based on `pk`)
            return redirect('sales-rep')  # Redirect to the product list after saving
    branch = Branch.objects.all() 
    view_context = {
        "form": form,
        "salesRep": salesRep,  
        "branch": branch,  
        "is_editing": bool(pk),  # Flag to indicate if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addSalesRep.html', context)


def update_salesRep_view(request, pk):
    salesRep = get_object_or_404(SalesAgent, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = SalesAgentForm(request.POST, instance=salesRep)  # Bind form to the product instance
        if form.is_valid():
            form.save()
            return redirect('sales-rep')  # Redirect to the product list
    else:
        form = SalesAgentForm(instance=salesRep)

    salesRep = SalesAgent.objects.all()
    branch = Branch.objects.all()  # For display in the list

    view_context = {
        "form": form,
        "salesRep": salesRep,
        "branch": branch,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addSalesRep.html', context)

def delete_salesRep_view(request, pk):
    """
    Handles deleting a crypto wallet.
    """
    salesRep = get_object_or_404(SalesAgent, id=pk)
    if request.method == "POST":
        salesRep.delete()
        return redirect("sales-rep")

    view_context = {
        "salesRep": salesRep,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteSalesRep.html', context)


@login_required
def get_sales_rep_credit_history(request, worker_id):
    """
    View to retrieve and display credit history for a worker with the role of Sales Rep.
    """
    # Get the worker and ensure they are a sales representative
    worker = get_object_or_404(Worker, id=worker_id, role="Sales Rep")

    # Fetch all credit invoices linked to this worker
    credit_invoices = OldInvoiceOrder.objects.filter(
        sales_rep=worker,  # Assuming sales_rep is linked to the Worker model
        payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid")  # Calculate amount due
    ).order_by("-created_at")
    
    current_invoice = credit_invoices.first()
    

    # Calculate total due for the sales rep
    total_due = credit_invoices.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0

    # Context data for the template
    view_context = {
        "worker": worker,
        "credit_invoices": credit_invoices,
        "current_invoice": current_invoice,
        "total_due": total_due,
    }
    
    context = TemplateLayout.init(request, view_context)
    

    return render(request, "salesRepCreditReport.html", context)