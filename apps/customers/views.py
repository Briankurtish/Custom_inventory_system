from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Customer
from .forms import CustomerForm

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageCustomerView(request):
    customers = Customer.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "customers": customers,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'customers.html', context)

def customer_view(request, pk=None):
    """
    Handles both adding and updating a customer.
    If pk is None, it creates a new customer; otherwise, it updates the existing customer.
    """
    customer = get_object_or_404(Customer, pk=pk) if pk else None
    form = CustomerForm(request.POST or None, request.FILES or None, instance=customer)
    
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('customers')  # Redirect to customer list or any desired page

    customers = Customer.objects.all()  # Fetch all customers for display

    view_context = {
        "form": form,
        "customers": customers,
        "is_editing": bool(pk),  # Determine if we're editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addCustomer.html', context)


def delete_customer_view(request, pk):
    """
    Handles deleting a crypto wallet.
    """
    customer = get_object_or_404(Customer, id=pk)
    if request.method == "POST":
        customer.delete()
        return redirect("customers")

    view_context = {
        "customer": customer,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteCustomer.html', context)