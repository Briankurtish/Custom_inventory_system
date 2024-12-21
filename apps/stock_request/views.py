from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib import messages
from .forms import StockRequestForm
from apps.products.models import Product
from apps.branches.models import Branch
from .models import StockRequest, StockRequestProduct, InTransit
from apps.stock.models import Stock
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.http import JsonResponse


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
                    "product_name": str(product.generic_name_dosage),
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
                # Create the main stock request
                branch = Branch.objects.get(id=temp_stock_request_list[0]["branch_id"])
                stock_request = StockRequest.objects.create(
                    branch=branch,
                    requested_by=request.user
                )

                for item in temp_stock_request_list:
                    product = Product.objects.get(product_code=item["product_code"])

                    # Add products to StockRequestProduct
                    StockRequestProduct.objects.create(
                        stock_request=stock_request,
                        product=product,
                        quantity=item["quantity"]
                    )

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

    # Prepare the context dictionary with the main stock requests
    view_context = {
        "stock_requests": stock_requests,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'requests.html', context)



@login_required
def stock_request_details(request, request_id):
    """
    View to get the details of a specific stock request.
    """
    stock_request = get_object_or_404(StockRequest, id=request_id)
    product_details = StockRequestProduct.objects.filter(stock_request=stock_request)

    view_context = {
        "stock_request": stock_request,
        "product_details": product_details,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'requestDetails.html', context)



@login_required
@transaction.atomic
def approve_or_decline_request(request, request_id):
    """
    Approve or decline a stock request. The central warehouse is treated as a special branch.
    """
    stock_request = get_object_or_404(StockRequest, id=request_id)
    
    if request.method == "POST":
        action = request.POST.get("action")  # 'approve' or 'decline'

        # Define central warehouse as a branch
        try:
            central_warehouse = Branch.objects.get(branch_type="central")  # Adjust field name as needed
        except Branch.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Central warehouse not found. Please ensure it exists."
            })

        if action == "approve":
            product_details = StockRequestProduct.objects.filter(stock_request=stock_request)
            
            for detail in product_details:
                product = detail.product
                quantity = detail.quantity

                # Check stock in the central warehouse
                central_stock = central_warehouse.stocks.filter(product=product).first()
                if not central_stock or central_stock.quantity < quantity:
                    return JsonResponse({
                        "success": False,
                        "message": f"Not enough stock for {product.generic_name_dosage} in the central warehouse."
                    })

                # Deduct stock from central warehouse
                central_stock.quantity -= quantity
                central_stock.save()

                # Add to the in-transit table and associate it with the stock request
                InTransit.objects.create(
                    product=product,
                    quantity=quantity,
                    source=central_warehouse.branch_name,
                    destination=stock_request.branch,
                    stock_request=stock_request  # Link the in-transit item to the stock request
                )
            
            # Update stock request status to "Accepted"
            stock_request.status = "Accepted"
            stock_request.save()

            return JsonResponse({
                "success": True,
                "message": "Stock request approved and items moved to in-transit."
            })
        
        elif action == "decline":
            # Update stock request status to "Rejected"
            stock_request.status = "Rejected"
            stock_request.save()

            return JsonResponse({
                "success": True,
                "message": "Stock request declined."
            })

    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })


@login_required
@transaction.atomic
def stock_received(request, request_id):
    """
    Handle stock reception by updating the branch warehouse and in-transit table.
    """
    # Get the stock request by ID
    stock_request = get_object_or_404(StockRequest, id=request_id)
    
    if request.method == "POST":
        # Get all in-transit items related to this stock request
        in_transit_items = InTransit.objects.filter(stock_request=stock_request)

        # Loop through each in-transit item and update stock in the branch warehouse
        for transit_item in in_transit_items:
            product = transit_item.product
            quantity = transit_item.quantity
            branch = transit_item.destination  # The branch that will receive the stock

            # Check if stock exists in the branch warehouse
            branch_stock = branch.stocks.filter(product=product).first()

            if branch_stock:
                # If stock exists, update the quantity
                branch_stock.quantity += quantity
                branch_stock.save()
            else:
                # If stock doesn't exist, create a new stock record
                Stock.objects.create(
                    product=product,
                    branch=branch,
                    quantity=quantity
                )
            
            # Mark the item as received in the in-transit table
            transit_item.delete()  # Optionally, you can just update the status field here if you want to keep records.

        # Update the stock request status to "Received"
        stock_request.status = "Received"
        stock_request.save()

        # Return a success message
        messages.success(request, "Stock received and branch warehouse updated successfully.")
        return redirect("requests")  # Redirect to the appropriate page, like the list of requests

    # If not a POST request, render a confirmation page or similar
    
    view_context = {
        "stock_request": stock_request,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'requests.html', context)
