from decimal import Decimal
from django.views.generic import TemplateView
from apps.orders.models import BankDeposit, Check, MomoInfo
from apps.products.models import Product
from web_project import TemplateLayout
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import OldInvoiceAuditLog, OldInvoiceOrder, OldInvoiceOrderItem, InvoicePaymentHistory
from apps.stock.models import Stock
from django.contrib import messages
from .forms import OldInvoiceOrderForm, OldInvoiceOrderItemForm, InvoicePaymentHistoryForm
from django.contrib.auth.decorators import login_required
from django.db import transaction  # For atomic operations
from apps.customers.models import Customer
from apps.branches.models import Branch
from apps.workers.models import Worker
from datetime import datetime
from django.core.paginator import Paginator
from django.db.models import F, Sum, ExpressionWrapper, DecimalField, FloatField
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Q




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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import OldInvoiceOrder, Branch

@login_required
def invoice_list(request):
    search_query = request.GET.get("search_query", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    branch_id = request.GET.get("branch")
    selected_month = request.GET.get("month")  # Get selected month from request

    # Fetch all branches for dropdown
    branches = Branch.objects.all()

    if request.user.is_superuser:
        old_invoice = OldInvoiceOrder.objects.all()
    else:
        user_branch = request.user.worker_profile.branch
        old_invoice = OldInvoiceOrder.objects.all()

    # Filter by date range if both start and end dates are provided
    if start_date and end_date:
        old_invoice = old_invoice.filter(created_at__date__range=[start_date, end_date])

    # Filter by selected branch
    if branch_id:
        old_invoice = old_invoice.filter(branch__id=branch_id)

    # Filter by selected month (if provided)
    if selected_month:
        old_invoice = old_invoice.filter(created_at__month=selected_month)

    # Apply search filtering
    if search_query:
        old_invoice = old_invoice.filter(
            Q(old_invoice_id__icontains=search_query) |
            Q(branch__branch_id__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(sales_rep__user__first_name__icontains=search_query) |
            Q(sales_rep__user__last_name__icontains=search_query) |
            Q(payment_method__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(amount_paid__icontains=search_query) |
            Q(amount_due__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

    # Order by most recent
    old_invoice = old_invoice.order_by("-created_at")

    # Pagination
    paginator = Paginator(old_invoice, 100)
    page_number = request.GET.get("page")
    paginated_orders = paginator.get_page(page_number)

    # Offset for numbering
    offset = (paginated_orders.number - 1) * paginator.per_page

    # List of months for dropdown selection
    months = [
        {"id": "1", "name": "January"},
        {"id": "2", "name": "February"},
        {"id": "3", "name": "March"},
        {"id": "4", "name": "April"},
        {"id": "5", "name": "May"},
        {"id": "6", "name": "June"},
        {"id": "7", "name": "July"},
        {"id": "8", "name": "August"},
        {"id": "9", "name": "September"},
        {"id": "10", "name": "October"},
        {"id": "11", "name": "November"},
        {"id": "12", "name": "December"},
    ]

    # Pass context to template
    view_context = {
        "old_invoice": paginated_orders,
        "search_query": search_query,
        "start_date": start_date,
        "end_date": end_date,
        "branches": branches,
        "branch_id": branch_id,  # Retain selected branch in template
        "offset": offset,
        "months": months,  # Pass months list to template
        "selected_month": selected_month,  # Retain selected month
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "OldInvoiceList.html", context)




@login_required
def OldInvoiceAuditLogView(request):
    logs = OldInvoiceAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "old_invoice_logs.html", context)


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
def old_invoice_details(request, invoice_id):
    worker_branch = request.user.worker_profile.branch

    # If user is superuser, allow them to view any invoice
    if request.user.is_superuser:
        old_invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id)
    else:
        # Regular users can only access invoices in their own branch
        old_invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id, branch=worker_branch)

    # Fetch the items associated with this invoice order
    invoice_items = OldInvoiceOrderItem.objects.filter(invoice_order=old_invoice).annotate(
        total_price=ExpressionWrapper(F('quantity') * F('price'), output_field=FloatField())
    )

    total_quantity = invoice_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Fetch the worker's privileges
    worker_privileges = request.user.worker_profile.privileges.values_list('name', flat=True)

    # Context for the template
    view_context = {
        "old_invoice": old_invoice,
        "invoice_items": invoice_items,
        "total_quantity": total_quantity,
        "worker_privileges": worker_privileges,
    }

    # Pass the context to the template layout and render the response
    context = TemplateLayout.init(request, view_context)
    return render(request, "invoiceDetails.html", context)





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
                "old_invoice_id": invoice_form.cleaned_data["old_invoice_id"],
                "branch": invoice_form.cleaned_data["branch"].id,
                "customer": invoice_form.cleaned_data["customer"].id,
                "sales_rep": invoice_form.cleaned_data["sales_rep"].id,
                "payment_method": invoice_form.cleaned_data["payment_method"],
                # "amount_paid": float(invoice_form.cleaned_data["amount_paid"]),
                "created_at": created_at_str,  # Saved as a string
            }
            return redirect("add_invoice_items")  # Redirect to add items to the order
        else:
            messages.error(request, _("Invalid form submission. Please correct the errors."))
    else:
        # Pass user_branch to the form initialization for filtering options
        invoice_form = OldInvoiceOrderForm(user_branch=user_branch)

    context = TemplateLayout.init(
        request,
        {"invoice_form": invoice_form}
    )
    return render(request, "createInvoiceOrder.html", context)


@login_required
def edit_invoice_order(request, invoice_id):
    """
    Edit an existing invoice order.
    """
    user_branch = request.user.worker_profile.branch

    # Fetch the invoice order
    if request.user.is_superuser:
        old_invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id)
    else:
        old_invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id, branch=user_branch)

    if request.method == "POST":
        # Use the form with the instance of the existing invoice order
        invoice_form = OldInvoiceOrderForm(data=request.POST, instance=old_invoice, user_branch=user_branch)

        if invoice_form.is_valid():
            updated_invoice = invoice_form.save(commit=False)
            updated_invoice.save()

            # Convert created_at datetime to string for JSON serialization
            created_at_str = updated_invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')

            # Save updated form data to the session
            request.session["invoice_order_details"] = {
                "old_invoice_id": updated_invoice.old_invoice_id,
                "branch": updated_invoice.branch.id,
                "customer": updated_invoice.customer.id,
                "sales_rep": updated_invoice.sales_rep.id,
                "payment_method": updated_invoice.payment_method,
                "created_at": created_at_str,  # Save as string
            }

            messages.success(request, _("Invoice updated successfully."))
            return redirect("edit-invoice-items", invoice_id=updated_invoice.id)  # Redirect to adding invoice items
        else:
            messages.error(request, _("Invalid form submission. Please correct the errors."))
    else:
        # Initialize form with existing invoice data
        invoice_form = OldInvoiceOrderForm(instance=old_invoice, user_branch=user_branch)

    context = TemplateLayout.init(
        request,
        {"invoice_form": invoice_form, "old_invoice": old_invoice}
    )
    return render(request, "editInvoiceOrder.html", context)


@login_required
def edit_invoice_items(request, invoice_id):
    """
    Edit items for an existing Old Invoice Order.
    """
    user_branch = request.user.worker_profile.branch

    # Fetch the invoice order
    if request.user.is_superuser:
        invoice_order = get_object_or_404(OldInvoiceOrder, id=invoice_id)
    else:
        invoice_order = get_object_or_404(OldInvoiceOrder, id=invoice_id, branch=user_branch)

    # Retrieve existing items from the database
    existing_items = OldInvoiceOrderItem.objects.filter(invoice_order=invoice_order)

    # Initialize session order items with existing data if not already present
    if "order_items" not in request.session or not request.session["order_items"]:
        request.session["order_items"] = [
            {
                "product_id": item.product.id,
                "product_name": str(item.product.generic_name_dosage),
                "price": str(item.price),  # Store as string to avoid serialization issues
                "quantity": item.quantity,
                "total_price": str(item.price * item.quantity),  # Store as string
            }
            for item in existing_items
        ]
        request.session.modified = True

    item_form = OldInvoiceOrderItemForm(user_branch=user_branch)

    if request.method == "POST":
        action = request.POST.get("action", "")
        order_items = request.session["order_items"]

        # Add item to order
        if action == "add_item":
            item_form = OldInvoiceOrderItemForm(data=request.POST, user_branch=user_branch)
            if item_form.is_valid():
                product = item_form.cleaned_data["product"]
                quantity = item_form.cleaned_data["quantity"]
                price = item_form.cleaned_data["price"]

                order_items.append({
                    "product_id": product.id,
                    "product_name": str(product.generic_name_dosage),
                    "price": str(price),  # Store as string
                    "quantity": quantity,
                    "total_price": str(price * quantity),  # Store as string
                })
                request.session.modified = True
                messages.success(request, f"Added {quantity} of {product.generic_name_dosage} to the order.")

        # Update an item in the order
        elif action == "update_item":
            try:
                item_index = int(request.POST.get("item_index", -1))
                quantity = int(request.POST.get("quantity"))
                price = Decimal(request.POST.get("price"))  # Convert to Decimal

                if 0 <= item_index < len(order_items):
                    order_items[item_index]["quantity"] = quantity
                    order_items[item_index]["price"] = str(price)  # Store as string
                    order_items[item_index]["total_price"] = str(price * quantity)  # Convert to string

                    request.session.modified = True
                    messages.success(request, _("Item updated successfully."))
                else:
                    messages.error(request, _("Invalid item index."))
            except ValueError:
                messages.error(request, _("Invalid input."))

        # Remove item from order
        elif action == "remove_item":
            try:
                item_index = int(request.POST.get("item_index", -1))
                if 0 <= item_index < len(order_items):
                    removed_item = order_items.pop(item_index)
                    request.session.modified = True
                    messages.success(request, f"Removed {removed_item['product_name']} from the order.")
                else:
                    messages.error(request, _("Invalid item index provided."))
            except ValueError:
                messages.error(request, _("Invalid item index provided."))

        # Submit updated order
        elif action == "submit_order":
            if order_items:
                try:
                    # Delete existing items before updating with new ones
                    OldInvoiceOrderItem.objects.filter(invoice_order=invoice_order).delete()

                    # Convert total price calculations to Decimal
                    grand_total = sum(Decimal(item["total_price"]) for item in order_items)

                    # Update the invoice order grand total
                    invoice_order.grand_total = grand_total
                    invoice_order.save()

                    # Add new items to the invoice order
                    for item in order_items:
                        product = get_object_or_404(Product, id=item["product_id"])
                        OldInvoiceOrderItem.objects.create(
                            invoice_order=invoice_order,
                            product=product,
                            quantity=item["quantity"],
                            price=Decimal(item['price']),  # Ensure price is Decimal
                        )

                    # Log the update action
                    try:
                        worker = request.user.worker_profile
                    except AttributeError:
                        worker = None

                    OldInvoiceAuditLog.objects.create(
                        user=worker,
                        action="update",
                        old_invoice=invoice_order.id,
                        branch=worker.branch.branch_name if worker else "",
                        details=f"Old Invoice record updated by: {worker}",
                    )

                    request.session["order_items"] = []
                    request.session.modified = True
                    messages.success(request, _("Old Invoice Items Updated Successfully."))
                    return redirect("old-invoice")
                except Exception as e:
                    messages.error(request, f"Error updating the invoice: {e}")
            else:
                messages.error(request, _("No items in the order."))

    # Calculate order details, ensuring total_price is converted to Decimal before summing
    order_items = request.session["order_items"]
    grand_total = sum(Decimal(item["total_price"]) for item in order_items)

    context = TemplateLayout.init(
        request,
        {
            "invoice_order": invoice_order,
            "item_form": item_form,
            "order_items": order_items,
            "grand_total": grand_total,
        }
    )
    return render(request, "editInvoiceOrderItems.html", context)





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
                product = item_form.cleaned_data["product"]
                quantity = item_form.cleaned_data["quantity"]
                price = item_form.cleaned_data["price"]

                # Add item to session without checking stock levels
                order_items = request.session["order_items"]
                order_items.append({
                    "product_id": product.id,
                    "product_name": str(product.generic_name_dosage),
                    "price": price,  # Convert Decimal to float
                    "quantity": quantity,
                    "total_price": float(price * quantity),
                })
                request.session.modified = True
                messages.success(request, f"Added {quantity} of {product.generic_name_dosage} to the order.")

        # Remove item from order
        elif action == "remove_item":
            try:
                item_index = int(request.POST.get("item_index", -1))
                order_items = request.session["order_items"]
                if 0 <= item_index < len(order_items):
                    removed_item = order_items.pop(item_index)
                    request.session.modified = True
                    messages.success(request, f"Removed {removed_item['product_name']} from the order.")
                else:
                    messages.error(request, _("Invalid item index provided."))
            except ValueError:
                messages.error(request, _("Invalid item index provided."))

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
                    old_invoice_id = invoice_order_details.get("old_invoice_id")
                    # amount_paid = invoice_order_details.get("amount_paid", 0.0)
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
                        old_invoice_id=old_invoice_id,
                        branch=branch,
                        customer=customer,
                        sales_rep=sales_rep,
                        payment_method=payment_method,
                        created_by=request.user.worker_profile,
                        grand_total=grand_total,
                        # amount_paid=amount_paid,
                        created_at=created_at,  # Save created_at date
                    )

                     # Log the submission action
                    try:
                        worker = request.user.worker_profile
                    except AttributeError:
                        worker = None
                    OldInvoiceAuditLog.objects.create(
                        user=worker,  # Assuming `request.user` is linked to a worker
                        action="create",
                        old_invoice=invoice_order.id,
                        branch=worker.branch.branch_name,
                        details=f"Old Invoice record created by: {worker}",
                    )

                    # Add items to the invoice order
                    for item in order_items:
                        product = get_object_or_404(Product, id=item["product_id"])
                        OldInvoiceOrderItem.objects.create(
                            invoice_order=invoice_order,
                            product=product,
                            quantity=item["quantity"],
                            price=item['price'],
                        )

                    # Clear session data
                    request.session["order_items"] = []
                    request.session["invoice_order_details"] = {}
                    request.session.modified = True
                    messages.success(request, _("Old Invoice Created Successfully."))
                    return redirect("old-invoice")
                except Exception as e:
                    messages.error(request, f"Error submitting the invoice: {e}")
            else:
                messages.error(request, _("No items in the order or missing order details."))

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
    return render(request, "addInvoiceOrderItems.html", context)


@login_required
def delete_old_invoice(request, invoice_id):
    """
    Deletes an old invoice order and its associated items.
    """
    invoice_order = get_object_or_404(OldInvoiceOrder, id=invoice_id)

    if request.method == "POST":

         # Log the submission action
        try:
            worker = request.user.worker_profile
        except AttributeError:
            worker = None
        OldInvoiceAuditLog.objects.create(
            user=worker,  # Assuming `request.user` is linked to a worker
            action="delete",
            old_invoice=invoice_order.id,
            branch=worker.branch.branch_name,
            details=f"Old Invoice record deleted by: {worker}",
        )
        invoice_order.delete()  # Automatically deletes related items due to CASCADE
        messages.success(request, "Old invoice deleted successfully.")
        return redirect("old-invoice")  # Redirect to invoice list page

    context = {
        "invoice_order": invoice_order
    }

    context = TemplateLayout.init(
        request,
        {
            "invoice_order": invoice_order
        }
    )
    return render(request, "deleteOldInvoice.html", context)


@login_required
def add_invoice_payment(request, invoice_id):
    """
    Handles the addition of a payment to an invoice.
    """
    invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id)

    if request.method == 'POST':
        form = InvoicePaymentHistoryForm(request.POST, invoice=invoice)

        if form.is_valid():
            payment_amount = form.cleaned_data['amount_paid']

            # Validate payment amount
            if payment_amount > invoice.grand_total:
                form.add_error('amount_paid', _("Payment amount cannot exceed the invoice's grand total."))
            elif payment_amount > invoice.amount_due:
                form.add_error('amount_paid', _("Payment amount cannot exceed the remaining amount due."))
            else:
                try:
                    with transaction.atomic():
                        # Save the payment
                        payment = form.save(commit=False)
                        payment.invoice = invoice
                        payment.invoice_total = invoice.grand_total  # Set the invoice total
                        payment.save()

                        # Update invoice amounts
                        invoice.amount_paid += payment.amount_paid
                        invoice.amount_due = max(invoice.grand_total - invoice.amount_paid, 0)
                        invoice.save()

                        # Log audit
                        worker = getattr(request.user, 'worker_profile', None)
                        OldInvoiceAuditLog.objects.create(
                            user=worker,
                            action="payment",
                            old_invoice=invoice.id,
                            branch=worker.branch.branch_name if worker else "Unknown Branch",
                            details=f"Old Invoice payment recorded by: {worker if worker else 'Unknown User'}",
                        )

                    messages.success(request, _("Payment added successfully!"))
                    return redirect('old-invoice')

                except Exception as e:
                    messages.error(request, _("An error occurred while processing the payment. Please try again."))
                    # Optional: Log the error for debugging
                    print(f"Error processing payment: {e}")

        else:
            messages.error(request, _("Error adding payment. Please check the form."))

    else:
        form = InvoicePaymentHistoryForm(invoice=invoice)

    # Prepare context and render form
    context = TemplateLayout.init(request, {
        'invoice': invoice,
        'form': form,
    })
    return render(request, 'addPayment.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .forms import InvoicePaymentHistoryForm
from .models import OldInvoiceOrder, InvoicePaymentHistory, OldInvoiceAuditLog

@login_required
def edit_invoice_payment(request, invoice_id, payment_id):
    """
    Handles the editing of a payment record for an invoice.
    """
    invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id)
    payment_history = get_object_or_404(InvoicePaymentHistory, id=payment_id, invoice=invoice)

    if request.method == 'POST':
        form = InvoicePaymentHistoryForm(request.POST, instance=payment_history, invoice=invoice)

        if form.is_valid():
            new_payment_amount = form.cleaned_data['amount_paid']
            old_payment_amount = payment_history.amount_paid  # Store old amount before update

            if new_payment_amount > invoice.grand_total:
                form.add_error('amount_paid', "Payment amount cannot exceed the invoice's grand total.")
            elif new_payment_amount < 0:
                form.add_error('amount_paid', "Payment amount cannot be negative.")
            else:
                try:
                    with transaction.atomic():
                        # Save the edited payment
                        payment = form.save(commit=False)
                        payment.invoice = invoice
                        payment.invoice_total = invoice.grand_total
                        payment.save()

                        # **Recalculate amount_paid & amount_due based on all records**
                        invoice.amount_paid = InvoicePaymentHistory.objects.filter(invoice=invoice).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
                        invoice.amount_due = max(invoice.grand_total - invoice.amount_paid, 0)
                        invoice.save(update_fields=["amount_paid", "amount_due"])

                        # Log the audit action
                        worker = getattr(request.user, 'worker_profile', None)
                        OldInvoiceAuditLog.objects.create(
                            user=worker,
                            action="payment_edit",
                            old_invoice=invoice.id,
                            branch=worker.branch.branch_name if worker else "Unknown Branch",
                            details=f"Payment for Invoice ID {invoice.id} edited by: {worker if worker else 'Unknown User'}",
                        )

                    messages.success(request, "Payment updated successfully!")
                    return redirect('old-invoice')

                except Exception as e:
                    messages.error(request, "An error occurred while updating the payment. Please try again.")
                    print(f"Error processing payment update: {e}")
        else:
            messages.error(request, "Error updating payment. Please check the form.")

    else:
        form = InvoicePaymentHistoryForm(instance=payment_history, invoice=invoice)

    context = TemplateLayout.init(
        request,
        {
            'form': form,
            'payment_history': payment_history,
            'invoice': invoice,
        }
    )

    return render(request, 'editPayment.html', context)







@login_required
def payment_history(request, invoice_id):
    """
    View to display the payment history for a specific invoice.
    """
    invoice = get_object_or_404(OldInvoiceOrder, id=invoice_id)

    # Recalculate amount_paid based on actual records
    amount_paid_aggregate = InvoicePaymentHistory.objects.filter(invoice=invoice).aggregate(Sum('amount_paid'))
    amount_paid = amount_paid_aggregate['amount_paid__sum'] or 0  # Default to 0 if no payments exist

    # Update the invoice amounts
    invoice.amount_paid = amount_paid
    invoice.amount_due = max(invoice.grand_total - invoice.amount_paid, 0)
    invoice.save(update_fields=["amount_paid", "amount_due"])

    # Get updated payment history
    payment_history = InvoicePaymentHistory.objects.filter(invoice=invoice).order_by('-payment_date')

    # Calculate percentages
    if invoice.grand_total > 0:  # Avoid division by zero
        percentage_paid = (invoice.amount_paid / invoice.grand_total) * 100
        percentage_left = (invoice.amount_due / invoice.grand_total) * 100
    else:
        percentage_paid = 0
        percentage_left = 0

    context = TemplateLayout.init(
        request,
        {
            'invoice': invoice,
            'payment_history': payment_history,
            'percentage_paid': round(percentage_paid, 2),  # Rounded to 2 decimal places
            'percentage_left': round(percentage_left, 2),  # Rounded to 2 decimal places
        }
    )
    return render(request, 'paymentHistory.html', context)




def get_accounts(request):
    payment_mode = request.GET.get('payment_mode')
    accounts = []

    if payment_mode == 'Mobile Money':
        accounts = MomoInfo.objects.values('id', 'momo_name')
    elif payment_mode == 'Check':
        accounts = Check.objects.values('id', 'bank__name')
    elif payment_mode == 'Bank Transfer':
        accounts = BankDeposit.objects.values('id', 'bank__name')

    # Prepare data for the frontend
    account_list = [{'id': acc['id'], 'name': acc['momo_name'] if 'momo_name' in acc else acc['bank__name']} for acc in accounts]
    return JsonResponse({'accounts': account_list})




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
