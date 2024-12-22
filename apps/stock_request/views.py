from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField
from .forms import StockRequestForm
from apps.products.models import Product
from apps.branches.models import Branch
from .models import StockRequest, StockRequestProduct, InTransit
from apps.stock.models import Stock
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.http import HttpResponseForbidden
from django.http import JsonResponse


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

TEMP_STOCK_REQUEST_LIST = [] 

@login_required
def stock_request_view(request):
    form = StockRequestForm(user=request.user)  # Pass the user to the form

    # Temporary stock request list handling
    temp_stock_request_list = request.session.get("TEMP_STOCK_REQUEST_LIST", [])

    if request.method == "POST":
        if "add_to_request_list" in request.POST:
            form = StockRequestForm(request.POST, user=request.user)  # Pass user when submitting form
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]

                # Check if the item already exists in the request list
                existing_item = next((item for item in temp_stock_request_list if item["product_code"] == product.product_code and item["branch_id"] == branch.id), None)
                
                if existing_item:
                    # If the item exists, update the quantity
                    existing_item["quantity"] += quantity
                else:
                    # Add new item if it does not exist
                    temp_stock_request_list.append({
                        "product_code": product.product_code,
                        "product_name": str(product.generic_name_dosage),
                        "quantity": quantity,
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                    })

                request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
                messages.success(request, "Item added to temporary stock request list.")
            else:
                messages.error(request, "Invalid data. Please check the form.")

        elif "remove_item" in request.POST:
            product_code = request.POST.get("product_code")
            branch_id = request.POST.get("branch")

            # Remove matching item from the temporary list
            temp_stock_request_list = [
                item for item in temp_stock_request_list 
                if not (item["product_code"] == product_code and item["branch_id"] == int(branch_id))
            ]
            request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
            messages.success(request, "Item removed from the temporary stock request list.")

        elif "submit_request" in request.POST:
            if temp_stock_request_list:
                branch = Branch.objects.get(id=temp_stock_request_list[0]["branch_id"])
                stock_request = StockRequest.objects.create(branch=branch, requested_by=request.user)

                for item in temp_stock_request_list:
                    product = Product.objects.get(product_code=item["product_code"])

                    StockRequestProduct.objects.create(stock_request=stock_request, product=product, quantity=item["quantity"])

                del request.session["TEMP_STOCK_REQUEST_LIST"]
                messages.success(request, "Stock request submitted successfully.")
                return redirect("requests")  # Adjust this with your actual URL name

    view_context = {
        "form": form,
        "temp_stock_request": temp_stock_request_list,
    }
    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)


    return render(request, 'createRequests.html', context)



def ManageRequestsView(request):
    # Get the user's worker profile and role
    worker_profile = getattr(request.user, 'worker_profile', None)
    
    if not worker_profile:
        return HttpResponseForbidden("You do not have access to manage stock requests.")
    
    user_role = worker_profile.role
    stock_requests = StockRequest.objects.all()

    # Check if the worker has the 'Request Stock' privilege
    can_request_stock = worker_profile.privileges.filter(name="Request Stock").exists()

    # Filter stock requests based on the user's role and privileges
    if user_role == "Marketing Director":
        # If the worker is a Marketing Director, show only requests created by them
        stock_requests = stock_requests.filter(requested_by=request.user)
    elif can_request_stock:
        # If the worker has the 'Request Stock' privilege, show only requests created by them
        stock_requests = stock_requests.filter(requested_by=request.user)
    elif user_role == "Stock Manager":
        # If the worker is a 'Stock Manager', show only accepted requests (status: "in transit")
        stock_requests = stock_requests.filter(status__iexact="in transit")

    # Get the selected status filter, defaulting to empty (no filter)
    status_filter = request.GET.get('status_filter', '')

    # Apply the status filter if it's provided
    if status_filter:
        stock_requests = stock_requests.filter(status__iexact=status_filter)

    # Order by requested_at to display the latest stock requests first
    stock_requests = stock_requests.order_by("-requested_at")

    # Prepare the context dictionary with the stock requests and privilege information
    view_context = {
        "stock_requests": stock_requests,
        "can_request_stock": can_request_stock,  # Include the privilege info
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    # Render the page with the provided context
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
            stock_request.status = "In Transit"
            stock_request.save()

            return redirect("requests")
        
        elif action == "decline":
            # Update stock request status to "Rejected"
            stock_request.status = "Rejected"
            stock_request.save()

            return redirect("requests")

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
            transit_item.status = "Received"
            transit_item.save()

        # Update the stock request status to "Received"
        stock_request.status = "Received"
        stock_request.save()

        # Return a success message
        messages.success(request, "Stock received and branch warehouse updated successfully.")
        return redirect("stock")  # Redirect to the appropriate page, like the list of requests

    else:
        # If not POST, show an error message or redirect
        messages.error(request, "Invalid request method.")
        return redirect("stock")

    # If not a POST request, render a confirmation page or similar
    
    view_context = {
        "stock_request": stock_request,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'requests.html', context)


@login_required
def stocks_in_transit(request):
    # Get the worker profile of the logged-in user
    worker = getattr(request.user, 'worker_profile', None)

    # If the user is not a worker or doesn't belong to a branch, deny access
    if not worker or not worker.branch:
        return HttpResponseForbidden("You do not have access to view stocks in transit.")

    # Retrieve the branch and in-transit stocks for the worker's branch
    branch = worker.branch
    stocks_in_transit = InTransit.objects.filter(destination=branch, status="In Transit")

    view_context = {
        'stocks_in_transit': stocks_in_transit,
        'branch_name': branch.branch_name,  # Pass the branch name to the template
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'transit-requests.html', context)