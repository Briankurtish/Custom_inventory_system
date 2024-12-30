from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import PurchaseOrder, PurchaseOrderItem
from apps.stock.models import Stock
from django.contrib import messages
from .forms import PurchaseOrderForm, PurchaseOrderItemForm
from django.contrib.auth.decorators import login_required
from django.db import transaction  # For atomic operations
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.utils.timezone import now
from datetime import timedelta
from apps.customers.models import Customer
from apps.branches.models import Branch
from apps.workers.models import Worker
from apps.oldinvoice.models import OldInvoiceOrder


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


# @login_required
# def order_list(request):
#     # Fetch orders associated with the user's branch or all if admin
#     user_branch = request.user.worker_profile.branch
#     if request.user.worker_profile.privileges == "View Orders":  # Adjust privileges check if needed
#         orders = PurchaseOrder.objects.all()
#     else:
#         orders = PurchaseOrder.objects.filter(branch=user_branch)

#     view_context = {
#         "orders": orders,
#     }
    
#     context = TemplateLayout.init(request, view_context)
    
#     return render(request, "orderList.html", context)


@login_required
def order_list(request):
    # Fetch the user's branch
    user_branch = request.user.worker_profile.branch

    # Fetch orders only for the user's branch
    orders = PurchaseOrder.objects.filter(branch=user_branch)

    # Prepare context for rendering
    view_context = {
        "orders": orders,
    }
    context = TemplateLayout.init(request, view_context)
    
    return render(request, "orderList.html", context)


@login_required
def order_details(request, order_id):
    # Fetch the purchase order and related items
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    order_items = PurchaseOrderItem.objects.filter(purchase_order=order)

    view_context = {
        "order": order,
        "order_items": order_items,
    }
    context = TemplateLayout.init(request, view_context)
    
    return render(request, "orderDetails.html", context)


@login_required
def credit_report(request, order_id):
    # Fetch the purchase order and related items
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    order_items = PurchaseOrderItem.objects.filter(purchase_order=order)

    view_context = {
        "order": order,
        "order_items": order_items,
    }
    context = TemplateLayout.init(request, view_context)
    
    return render(request, "customerCreditReport.html", context)


@login_required
def create_purchase_order(request):
    user_branch = request.user.worker_profile.branch

    if request.method == "POST":
        # Create form instance, passing the user's branch to limit branch selection
        po_form = PurchaseOrderForm(data=request.POST, user_branch=user_branch)
        
        if po_form.is_valid():
            # Save the form data to the session instead of creating the purchase order immediately
            request.session["purchase_order_details"] = {
                "branch": user_branch.id,  # Save the branch ID for later use
                "customer": po_form.cleaned_data["customer"].id,  # Save customer ID
                "sales_rep": po_form.cleaned_data["sales_rep"].id,  # Save sales rep ID
                "payment_method": po_form.cleaned_data["payment_method"],  # Save payment method
            }

            # Redirect to the page for adding order items
            return redirect("add_order_items")
        else:
            messages.error(request, "Invalid form submission. Please correct the errors.")
    else:
        po_form = PurchaseOrderForm(user_branch=user_branch)

    view_context = {
        "po_form": po_form,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "createPurchaseOrder.html", context)

@login_required
def add_order_items(request):
    user_branch = request.user.worker_profile.branch

    # Initialize session data if it doesn't exist
    if "order_items" not in request.session:
        request.session["order_items"] = []

    # Initialize the form for both GET and POST methods
    item_form = PurchaseOrderItemForm(user_branch=user_branch)

    if request.method == "POST":
        action = request.POST.get("action", "")

        # Add item to order
        if action == "add_item":
            item_form = PurchaseOrderItemForm(data=request.POST, user_branch=user_branch)
            if item_form.is_valid():
                stock = item_form.cleaned_data["stock"]
                quantity = item_form.cleaned_data["quantity"]

                # Ensure stock availability
                if quantity > stock.quantity:
                    messages.error(request, f"Insufficient stock: only {stock.quantity} available.")
                else:
                    # Add item to session
                    order_items = request.session["order_items"]
                    order_items.append({
                        "stock_id": stock.id,
                        "stock_name": str(stock.product.generic_name_dosage),
                        "unit_price": float(stock.product.unit_price),  # Convert Decimal to float
                        "quantity": quantity,
                        "total_price": float(stock.product.unit_price * quantity),
                    })
                    request.session.modified = True
                    messages.success(request, f"Added {quantity} of {stock.product.generic_name_dosage} to the order.")
            else:
                messages.error(request, "Invalid form input. Please correct the errors.")

        # Remove item from order
        elif action == "remove_item":
            try:
                # Get item index from POST data
                item_index = int(request.POST.get("item_index", -1))
                order_items = request.session["order_items"]

                # Ensure index is valid
                if 0 <= item_index < len(order_items):
                    removed_item = order_items.pop(item_index)
                    request.session.modified = True  # Mark session as modified

                    # Notify success
                    messages.success(request, f"Removed {removed_item['stock_name']} from the order.")
                else:
                    messages.error(request, "Invalid item index provided.")
            except ValueError:
                messages.error(request, "Invalid item index provided.")

        # Submit order
        elif action == "submit_order":
            order_items = request.session["order_items"]
            if order_items:
                try:
                    # Retrieve customer, sales_rep, and payment_method from session
                    purchase_order_details = request.session.get("purchase_order_details", {})

                    customer_id = purchase_order_details.get("customer")
                    sales_rep_id = purchase_order_details.get("sales_rep")
                    payment_method = purchase_order_details.get("payment_method")
                    branch_id = purchase_order_details.get("branch")

                    # Retrieve related objects
                    customer = get_object_or_404(Customer, id=customer_id)
                    sales_rep = get_object_or_404(Worker, id=sales_rep_id)
                    branch = get_object_or_404(Branch, id=branch_id)

                    # Calculate the grand total
                    grand_total = sum(item["unit_price"] * item["quantity"] for item in order_items)

                    # Create purchase order with status 'Pending' and calculated grand total
                    purchase_order = PurchaseOrder.objects.create(
                        branch=branch,
                        customer=customer,
                        sales_rep=sales_rep,
                        payment_method=payment_method,
                        created_by=request.user.worker_profile,
                        status="Pending",
                        grand_total=grand_total,
                    )

                    # Add items to the purchase order
                    for item in order_items:
                        stock = get_object_or_404(Stock, id=item["stock_id"])
                        PurchaseOrderItem.objects.create(
                            purchase_order=purchase_order,
                            stock=stock,
                            quantity=item["quantity"],
                        )
                        # Update stock quantity
                        stock.quantity -= item["quantity"]
                        stock.save()

                    # Clear session data and redirect
                    request.session["order_items"] = []
                    request.session.modified = True
                    messages.success(request, "Purchase order submitted successfully.")
                    return redirect("orders")
                except Exception as e:
                    messages.error(request, f"Error submitting the order: {e}")
            else:
                messages.error(request, "No items in the order to submit.")

    # Calculate order details
    order_items = request.session["order_items"]
    grand_total = sum(item["unit_price"] * item["quantity"] for item in order_items)

    view_context = {
        "item_form": item_form,
        "order_items": order_items,
        "grand_total": grand_total,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "addOrderItems.html", context)




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






# @login_required
# def create_purchase_order(request):
#     user_branch = request.user.worker_profile.branch
#     user_worker = request.user.worker_profile

#     # Temporary list for order items during the request
#     temp_order_items = []

#     # Initialize forms
#     po_form = PurchaseOrderForm(user_branch=user_branch)
#     item_form = PurchaseOrderItemForm(user_branch=user_branch)

#     # Handle POST requests
#     if request.method == "POST":
#         action = request.POST.get("action", "")

#         # Bind data to forms only for relevant actions
#         if action in ["add_item", "submit_order"]:
#             po_form = PurchaseOrderForm(data=request.POST, user_branch=user_branch)
#             item_form = PurchaseOrderItemForm(data=request.POST, user_branch=user_branch)

#         if action == "add_item" and item_form.is_valid():
#             # Get item data
#             stock = item_form.cleaned_data["stock"]
#             quantity = item_form.cleaned_data["quantity"]

#             # Check if stock already exists in the list
#             for item in temp_order_items:
#                 if item["stock_id"] == stock.id:
#                     item["quantity"] += quantity
#                     messages.success(request, f"Updated quantity for {stock.product.generic_name_dosage}.")
#                     break
#             else:
#                 # Add a new item to the list
#                 temp_order_items.append({
#                     "stock_id": stock.id,
#                     "stock_name": str(stock.product.generic_name_dosage),
#                     "quantity": quantity,
#                 })
#                 messages.success(request, f"Added {quantity} of {stock.product.generic_name_dosage} to the order.")

#         elif action == "remove_item":
#             stock_id = int(request.POST.get("stock_id", -1))
#             temp_order_items = [item for item in temp_order_items if item["stock_id"] != stock_id]
#             messages.success(request, "Item removed from the order.")

#         elif action == "submit_order" and po_form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # Create the purchase order
#                     purchase_order = po_form.save(commit=False)
#                     purchase_order.branch = user_branch
#                     purchase_order.created_by = user_worker
#                     purchase_order.save()

#                     # Save items to the database
#                     for item in temp_order_items:
#                         stock = Stock.objects.get(id=item["stock_id"])
#                         quantity = item["quantity"]

#                         if quantity > stock.quantity:
#                             raise ValueError(f"Insufficient stock for {stock.product.generic_name_dosage}.")

#                         # Create purchase order items and update stock
#                         PurchaseOrderItem.objects.create(
#                             purchase_order=purchase_order,
#                             stock=stock,
#                             quantity=quantity,
#                         )
#                         stock.quantity -= quantity
#                         stock.save()

#                     messages.success(request, "Purchase order created successfully.")
#                     return redirect("orders")

#             except ValueError as e:
#                 messages.error(request, str(e))
#             except Exception as ex:
#                 messages.error(request, "An error occurred while creating the purchase order.")

#     # Enhanced items for display
#     enhanced_items = []
#     grand_total = 0

#     for item in temp_order_items:
#         stock = Stock.objects.get(id=item["stock_id"])
#         unit_price = stock.product.unit_price
#         total_price = unit_price * item["quantity"]
#         grand_total += total_price

#         enhanced_items.append({
#             "stock": stock,
#             "quantity": item["quantity"],
#             "unit_price": unit_price,
#             "total_price": total_price,
#         })

#     # Prepare context
#     view_context = {
#         "po_form": po_form,
#         "item_form": item_form,
#         "user_branch": user_branch,
#         "order_items": enhanced_items,
#         "grand_total": grand_total,
#     }
    
#     context = TemplateLayout.init(request, view_context)
    

#     return render(request, "createOrder.html", context)
