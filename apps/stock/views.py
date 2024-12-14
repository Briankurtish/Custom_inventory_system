from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import StockUpdateForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from apps.products.models import Product

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

# Temp storage for demonstration; use sessions or database in production
TEMP_STOCK_LIST = []  

def update_stock_view(request):
    products = Product.objects.all()
    form = StockUpdateForm()
    global TEMP_STOCK_LIST
    
    if request.method == "POST":
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            # Extract data
            product_code = form.cleaned_data["product_code"]
            quantity = form.cleaned_data["quantity"]
            branch = form.cleaned_data["branch"]

            # Add to temporary stock list
            TEMP_STOCK_LIST.append({
                "product_code": product_code,
                "quantity": quantity,
                "branch_id": branch.id,
                "branch_name": branch.branch_name,
            })
            messages.success(request, "Item added to temporary stock list.")
            return redirect("update-stock")  # Replace with your URL name
    else:
        form = StockUpdateForm()
        
    view_context = {
        "form": form,
        "temp_stock": TEMP_STOCK_LIST,
        "products": products,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'updateStock.html', context)