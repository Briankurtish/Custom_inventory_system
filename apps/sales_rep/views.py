from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import SalesAgent
from .forms import SalesAgentForm
from apps.branches.models import Branch


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageSalesRepView(request):
    salesRep = SalesAgent.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "salesRep": salesRep,
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