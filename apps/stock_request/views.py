from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib import messages
from .forms import StockRequestForm
from apps.products.models import Product
from apps.branches.models import Branch
from .models import StockRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

TEMP_STOCK_REQUEST_LIST = [] 

@login_required
def stock_request_view(request):
    # Initialize form and temporary list
    form = StockRequestForm()
    temp_stock_request_list = request.session.get("TEMP_STOCK_REQUEST_LIST", [])

    if request.method == "POST":
        if "add_to_request_list" in request.POST:  # Handle adding to the temporary stock request list
            form = StockRequestForm(request.POST)
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]

                # Add item to temporary stock request list
                temp_stock_request_list.append({
                    "product_code": product.product_code,
                    "product_name": str(product.generic_name_dosage),  # Convert to string
                    "quantity": quantity,
                    "branch_id": branch.id,
                    "branch_name": branch.branch_name,
                })
                # Store the updated temporary list in session
                request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
                messages.success(request, "Item added to temporary stock request list.")
            else:
                messages.error(request, "Invalid data. Please check the form.")

        elif "remove_item" in request.POST:  # Handle removing from the temporary stock request list
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")

            # Remove matching item from the temporary list
            temp_stock_request_list = [
                item for item in temp_stock_request_list 
                if not (item["product_code"] == product_code and item["branch_id"] == int(branch_id))
            ]
            # Store the updated list in session
            request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
            messages.success(request, "Item removed from the temporary stock request list.")

        elif "submit_request" in request.POST:  # Handle submitting the stock request
            if temp_stock_request_list:
                for item in temp_stock_request_list:
                    product = Product.objects.get(product_code=item["product_code"])
                    branch = Branch.objects.get(id=item["branch_id"])

                    # Create the stock request
                    stock_request = StockRequest.objects.create(
                        product=product,
                        branch=branch,
                        quantity=item["quantity"],
                        requested_by=request.user  # Attach the logged-in user
                    )

                    messages.info(request, f"Stock request created for product {product.generic_name_dosage}.")
                
                # Clear the temporary list after submitting the request
                del request.session["TEMP_STOCK_REQUEST_LIST"]
                messages.success(request, "Stock request submitted successfully.")
                return redirect("requests")  # Replace with the correct URL name for success page
            else:
                messages.warning(request, "No items in the temporary stock request list to submit.")

    # Prepare context for rendering
    view_context = {
        "form": form,
        "temp_stock_request": temp_stock_request_list,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'createRequests.html', context)


def ManageRequestsView(request):
    stock_requests = StockRequest.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "stock_requests": stock_requests,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'requests.html', context)