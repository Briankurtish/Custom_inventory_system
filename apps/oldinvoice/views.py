from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import OldInvoiceOrder, OldInvoiceOrderItem
from apps.stock.models import Stock
from django.contrib import messages
from .forms import OldInvoiceOrderForm, OldInvoiceOrderItemForm
from django.contrib.auth.decorators import login_required
from django.db import transaction  # For atomic operations
from apps.customers.models import Customer
from apps.branches.models import Branch
from apps.workers.models import Worker
from datetime import datetime


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
def invoice_list(request):
    # Fetch the user's branch
    user_branch = request.user.worker_profile.branch

    # Fetch orders only for the user's branch
    orders = OldInvoiceOrder.objects.filter(branch=user_branch)

    # Prepare context for rendering
    view_context = {
        "orders": orders,
    }
    context = TemplateLayout.init(request, view_context)
    
    return render(request, "invoiceList.html", context)


# @login_required
# def order_details(request, order_id):
#     # Fetch the purchase order and related items
#     order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

#     order_items = PurchaseOrderItem.objects.filter(purchase_order=order)

#     view_context = {
#         "order": order,
#         "order_items": order_items,
#     }
#     context = TemplateLayout.init(request, view_context)
    
#     return render(request, "orderDetails.html", context)




@login_required
def create_invoice_order(request):
    """
    Create an invoice order and save the form data temporarily in the session.
    """
    user_branch = request.user.worker_profile.branch

    if request.method == "POST":
        # Use a form class to validate and process the data
        invoice_form = OldInvoiceOrderForm(data=request.POST, user_branch=user_branch)

        if invoice_form.is_valid():
            # Convert the created_at datetime to string for JSON serialization
            created_at = invoice_form.cleaned_data["created_at"]
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            

            # Save form data to the session
            request.session["invoice_order_details"] = {
                "branch": user_branch.id,
                "customer": invoice_form.cleaned_data["customer"].id,
                "sales_rep": invoice_form.cleaned_data["sales_rep"].id,
                "payment_method": invoice_form.cleaned_data["payment_method"],
                "amount_paid": float(invoice_form.cleaned_data["amount_paid"]),
                "created_at": created_at_str,  # Saved as a string
            }
            return redirect("add_invoice_items")  # Redirect to add items to the order
        else:
            messages.error(request, "Invalid form submission. Please correct the errors.")
    else:
        # Pass user_branch to the form initialization for filtering options
        invoice_form = OldInvoiceOrderForm(user_branch=user_branch)

    context = TemplateLayout.init(
        request,
        {"invoice_form": invoice_form}
    )
    return render(request, "createInvoiceOrder.html", context)


@login_required
def add_invoice_items(request):
    user_branch = request.user.worker_profile.branch

    # Initialize session data if it doesn't exist
    if "order_items" not in request.session:
        request.session["order_items"] = []

    item_form = OldInvoiceOrderItemForm(user_branch=user_branch)

    if request.method == "POST":
        action = request.POST.get("action", "")

        # Add item to order
        if action == "add_item":
            item_form = OldInvoiceOrderItemForm(data=request.POST, user_branch=user_branch)
            if item_form.is_valid():
                stock = item_form.cleaned_data["stock"]
                quantity = item_form.cleaned_data["quantity"]

                # Add item to session without checking stock levels
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

        # Remove item from order
        elif action == "remove_item":
            try:
                item_index = int(request.POST.get("item_index", -1))
                order_items = request.session["order_items"]
                if 0 <= item_index < len(order_items):
                    removed_item = order_items.pop(item_index)
                    request.session.modified = True
                    messages.success(request, f"Removed {removed_item['stock_name']} from the order.")
                else:
                    messages.error(request, "Invalid item index provided.")
            except ValueError:
                messages.error(request, "Invalid item index provided.")

        # Submit order
        elif action == "submit_order":
            order_items = request.session.get("order_items", [])
            invoice_order_details = request.session.get("invoice_order_details", {})

            if order_items and invoice_order_details:
                try:
                    # Retrieve customer, sales_rep, payment_method, created_at, and branch from session
                    customer_id = invoice_order_details.get("customer")
                    sales_rep_id = invoice_order_details.get("sales_rep")
                    payment_method = invoice_order_details.get("payment_method")
                    branch_id = invoice_order_details.get("branch")
                    amount_paid = invoice_order_details.get("amount_paid", 0.0)
                    created_at_str = invoice_order_details.get("created_at")  # Retrieve created_at string

                    # Convert created_at from string back to datetime
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')  # Convert string back to datetime

                    # Retrieve related objects
                    customer = get_object_or_404(Customer, id=customer_id)
                    sales_rep = get_object_or_404(Worker, id=sales_rep_id)
                    branch = get_object_or_404(Branch, id=branch_id)

                    # Calculate the grand total
                    grand_total = sum(item["total_price"] for item in order_items)

                    # Create the invoice order
                    invoice_order = OldInvoiceOrder.objects.create(
                        branch=branch,
                        customer=customer,
                        sales_rep=sales_rep,
                        payment_method=payment_method,
                        created_by=request.user.worker_profile,
                        grand_total=grand_total,
                        amount_paid=amount_paid,
                        created_at=created_at,  # Save created_at date
                    )

                    # Add items to the invoice order
                    for item in order_items:
                        stock = get_object_or_404(Stock, id=item["stock_id"])
                        OldInvoiceOrderItem.objects.create(
                            invoice_order=invoice_order,
                            stock=stock,
                            quantity=item["quantity"],
                        )

                    # Clear session data
                    request.session["order_items"] = []
                    request.session["invoice_order_details"] = {}
                    request.session.modified = True
                    messages.success(request, "Invoice order submitted successfully.")
                    return redirect("old-invoice")
                except Exception as e:
                    messages.error(request, f"Error submitting the invoice: {e}")
            else:
                messages.error(request, "No items in the order or missing order details.")

    # Calculate order details
    order_items = request.session["order_items"]
    grand_total = sum(item["total_price"] for item in order_items)

    context = TemplateLayout.init(
        request,
        {
            "item_form": item_form,
            "order_items": order_items,
            "grand_total": grand_total,
        }
    )
    return render(request, "addOrderItems.html", context)












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
