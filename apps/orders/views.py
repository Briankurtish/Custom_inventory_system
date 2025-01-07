from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import PurchaseOrder, PurchaseOrderItem, TemporaryStock, InvoiceOrderItem, Invoice, InvoicePayment, Receipt
from apps.stock.models import Stock
from django.contrib import messages
from .forms import PurchaseOrderForm, PurchaseOrderItemForm, InvoicePaymentForm
from django.contrib.auth.decorators import login_required
from django.db import transaction  # For atomic operations
from django.db.models import F, Sum, ExpressionWrapper, DecimalField
from django.utils.timezone import now
from datetime import timedelta
from apps.customers.models import Customer
from apps.branches.models import Branch
from apps.workers.models import Worker
from apps.oldinvoice.models import OldInvoiceOrder
from django.core.paginator import Paginator
from django.db.models import F, FloatField, ExpressionWrapper, Case, When, Value
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from django.db.models import Q
from django.utils import timezone


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

    # Get the status filter from the query parameters
    status_filter = request.GET.get("status")

    # Filter orders by branch and optionally by status
    orders = PurchaseOrder.objects.filter(branch=user_branch)
    if status_filter:
        orders = orders.filter(status__iexact=status_filter)

    # Order by 'Pending' first and then by creation date
    orders = orders.order_by(
        Case(
            When(status__iexact="Pending", then=Value(0)),
            default=Value(1),
        ),
        "-created_at",
    )

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")  # Get the current page number from the request
    paginated_orders = paginator.get_page(page_number)

    # Prepare context for rendering
    view_context = {
        "orders": paginated_orders,
        "status_filter": status_filter,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "orderList.html", context)


@login_required
def invoice_list(request):
    # Fetch the user's branch
    user_branch = request.user.worker_profile.branch

    # Fetch orders only for the user's branch
    invoices = Invoice.objects.filter(branch=user_branch)
    
    # Count unpaid invoices
    
    
    paginator = Paginator(invoices, 10) 
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_invoice = paginator.get_page(page_number)

    # Prepare context for rendering
    view_context = {
        "invoices": paginated_invoice,
        
    }
    context = TemplateLayout.init(request, view_context)
    
    return render(request, "invoiceList.html", context)


@login_required
def order_details(request, order_id):
    # Fetch the purchase order and related items
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

     # Annotate the total price for each item (quantity * temp price or unit price)
    order_items = PurchaseOrderItem.objects.filter(purchase_order=order).annotate(
        effective_price=Case(
            When(temp_price__isnull=False, then=F('temp_price')),
            default=F('stock__product__unit_price'),
            output_field=FloatField()
        ),
        total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
    )
    
     # Calculate total quantity
    total_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    
    # Fetch the worker's privileges
    worker = request.user.worker_profile
    worker_privileges = worker.privileges.values_list('name', flat=True)

    # Context for the template
    view_context = {
        "order": order,
        "order_items": order_items,
         "total_quantity": total_quantity,
        'worker_privileges': worker_privileges,
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
def payment_history(request, invoice_id):
    """
    View to display the payment history for a specific invoice.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    payment_history = InvoicePayment.objects.filter(invoice=invoice).order_by('-payment_date')

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
    return render(request, 'paymentInvoiceHistory.html', context)



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


from decimal import Decimal
from django.db import transaction

def approve_order(request, order_id):
    # Fetch the order
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    notes = request.POST.get('notes', '').strip()
    if not notes:
        messages.error(request, "Approval notes are required.")
        return redirect(reverse('order_details', args=[order_id]))
    
    # Check if the order is already approved or rejected
    if order.status != 'Pending':
        messages.error(request, "This order has already been processed.")
        return redirect(reverse('order_details', args=[order_id]))

    try:
        with transaction.atomic():
            # Deduct stock and move items to TemporaryStock
            for item in order.items.all():
                stock = item.stock
                item_quantity = item.quantity
                item_effective_price = item.get_effective_price()

                # Check if there is enough stock to fulfill the order
                if stock.quantity < item_quantity:
                    messages.error(request, f"Insufficient stock for {stock.product.product_code}.")
                    return redirect(reverse('order_details', args=[order_id]))

                # Deduct stock
                stock.quantity -= item_quantity
                stock.save()

                # Add the item to the temporary stock
                TemporaryStock.objects.create(
                    purchase_order=order,
                    stock=stock,
                    ordered_quantity=item_quantity
                )

            # Update the status of the order to 'Approved'
            order.status = 'Approved'
            order.approved_by = request.user.worker_profile  # Assign Worker instance to approved_by
            order.notes = f"[Approval Note]: {notes} ({timezone.now().strftime('%Y-%m-%d %H:%M:%S')})"   
            order.save()

            # Generate an invoice for the approved order
            invoice = Invoice.objects.create(
                branch=order.branch,
                customer=order.customer,
                sales_rep=order.sales_rep,
                payment_method=order.payment_method,
                created_by=request.user.worker_profile,  # Assign Worker instance to created_by
                purchase_order=order,
                grand_total=order.grand_total,  # The total amount from the purchase order
                amount_paid=Decimal('0.00'),  # Assuming no payment is made at this point
                amount_due=order.grand_total  # Assuming the full amount is due at this point
            )

            # Create invoice items
            for item in order.items.all():
                InvoiceOrderItem.objects.create(
                    invoice_order=invoice,
                    stock=item.stock,
                    quantity=item.quantity,
                    price=item.get_effective_price()  # Use the effective price (temp price or regular price)
                )

            messages.success(request, "Order approved and invoice generated successfully.")
            return redirect(reverse('order_details', args=[order_id]))

    except Exception as e:
        # Handle any unexpected exceptions and roll back the transaction
        transaction.rollback()
        messages.error(request, f"An error occurred while approving the order: {str(e)}")
        return redirect(reverse('order_details', args=[order_id]))







@login_required
def generate_purchase_order_pdf(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id)
    # order_items = PurchaseOrderItem.objects.filter(purchase_order=order)
    
     # Annotate the total price for each item (quantity * temp price or unit price)
    order_items = PurchaseOrderItem.objects.filter(purchase_order=order).annotate(
        effective_price=Case(
            When(temp_price__isnull=False, then=F('temp_price')),
            default=F('stock__product__unit_price'),
            output_field=FloatField()
        ),
        total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
    )

    # Prepare data for the template
    context = {
        "order": order,
        "order_items": order_items,
    }

    # Render the HTML template to a string
    html_content = render_to_string("purchase_order.html", context)

    # Create a PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type="application/pdf")
    else:
        return HttpResponse("Error generating PDF", status=400)


@login_required
def reject_order(request, order_id):
    # Fetch the order
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    # Check if the order is already approved or rejected
    if order.status != 'Pending':
        messages.error(request, "This order has already been processed.")
        return redirect(reverse('order_details', args=[order_id]))

    if request.method == 'POST':
        # Get the rejection reason
        notes = request.POST.get('notes', '').strip()
        if not notes:
            messages.error(request, "Rejection notes are required.")
            return redirect(reverse('order_details', args=[order_id]))

        # Update order status and notes
        order.status = 'Rejected'
        order.notes = notes
        order.save()

        messages.success(request, "Order rejected successfully.")
        return redirect(reverse('order_details', args=[order_id]))
    
    # If not POST, return error response
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def cancel_order(request, order_id):
    # Fetch the order
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    # Ensure the order is approved before allowing cancellation
    if order.status != 'Approved':
        messages.error(request, "Only approved orders can be canceled.")
        return redirect(reverse('order_details', args=[order_id]))

    # Perform cancellation
    if request.method == 'POST':
        try:
            # Iterate through the items in the order
            order_items = PurchaseOrderItem.objects.filter(purchase_order=order)
            for item in order_items:
                stock = item.stock

                # Restore the stock quantity
                stock.quantity += item.quantity
                stock.save()

                # Remove the item from the TemporaryStock table
                TemporaryStock.objects.filter(
                    purchase_order=order,
                    stock=stock
                ).delete()

            # Update the order status to "Canceled"
            order.status = 'Canceled'
            order.save()

            messages.success(request, "Order canceled and stock levels restored successfully.")
            return redirect(reverse('order_details', args=[order_id]))

        except Exception as e:
            messages.error(request, f"An error occurred while canceling the order: {e}")
            return redirect(reverse('order_details', args=[order_id]))

    # If not POST, return an error response
    return JsonResponse({'error': 'Invalid request method'}, status=400)




@login_required
def edit_prices(request, order_id):
    if request.method == "POST":
        # Fetch the order items for the given order
        order_items = PurchaseOrderItem.objects.filter(purchase_order_id=order_id)
        order = get_object_or_404(PurchaseOrder, id=order_id)

        try:
            with transaction.atomic():
                # Capture the reason for price change
                edit_price_note = request.POST.get("edit_price_note", "").strip()
                if not edit_price_note:
                    messages.error(request, "Please provide a reason for the price change.")
                    return redirect("order_details", order_id=order_id)

                for item in order_items:
                    # Extract and update the temporary price for each item
                    new_price = request.POST.get(f"prices[{item.id}]")
                    if new_price:
                        new_price = float(new_price)
                        if new_price < 0:
                            raise ValueError(f"Price for item {item.id} cannot be negative.")
                        item.temp_price = new_price
                        item.save()

                # Recalculate the grand total for the order
                grand_total = order_items.annotate(
                    effective_price=Case(
                        When(temp_price__isnull=False, then=F('temp_price')),
                        default=F('stock__product__unit_price'),
                        output_field=FloatField()
                    ),
                    total_price=F('quantity') * F('effective_price')
                ).aggregate(total=Sum('total_price'))['total']

                # Update the grand total in the order
                order.grand_total = grand_total

                # Overwrite the note with the new reason
                order.notes = f"[Price Change]: {edit_price_note} ({timezone.now().strftime('%Y-%m-%d %H:%M:%S')})"
                order.save()

                messages.success(request, "Prices and grand total updated successfully for this order.")
        except Exception as e:
            messages.error(request, f"An error occurred while updating prices: {e}")

        return redirect("order_details", order_id=order_id)
    else:
        return redirect("orders")





@login_required
def get_customer_report(request, customer_id):
    """
    View to retrieve and display a specific customer's credit history from OldInvoiceOrder and Invoice in two tables.
    """
    # Get the customer object
    customer = get_object_or_404(Customer, id=customer_id)

    # Fetch old credit orders from OldInvoiceOrder
    old_credit_orders = OldInvoiceOrder.objects.filter(
        customer=customer, payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid"),
    ).order_by("-created_at")

    # Fetch current credit orders from Invoice
    current_credit_orders = Invoice.objects.filter(
        customer=customer, payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid"),
    ).order_by("-created_at")
    
    current_invoice = current_credit_orders.first()

    # Calculate total dues for both tables
    total_due_old = old_credit_orders.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    total_due_current = current_credit_orders.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    
    total_due_general = total_due_old + total_due_current

    # Prepare context for the template
    view_context = {
        "customer": customer,
        "current_invoice": current_invoice,
        "old_credit_orders": old_credit_orders,
        "current_credit_orders": current_credit_orders,
        "total_due_old": total_due_old,
        "total_due_current": total_due_current,
        "total_due_general": total_due_general,
         "current_date": now(),
        
    }

    # Use TemplateLayout for consistent UI
    context = TemplateLayout.init(request, view_context)
    return render(request, "CreditReport.html", context)




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
    
    # Fetch current credit orders from Invoice
    current_credit_orders = Invoice.objects.filter(
        sales_rep=worker, payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid"),
    ).order_by("-created_at")
    
    current_invoice = current_credit_orders.first()
    

    # Calculate total due for the sales rep
    total_due_old = credit_invoices.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    total_due_current = current_credit_orders.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    
    total_due_general = total_due_old + total_due_current
    

    # Context data for the template
    view_context = {
        "worker": worker,
        "credit_invoices": credit_invoices,
        "current_credit_orders": current_credit_orders,
        "current_invoice": current_invoice,
        "total_due_old": total_due_old,
        "total_due_current": total_due_current,
        "total_due_general": total_due_general,
         "current_date": now(),
    }
    
    context = TemplateLayout.init(request, view_context)
    

    return render(request, "salesRepCreditReport.html", context)


@login_required
def add_invoice_payment(request, invoice_id):
    """
    Handles adding a payment and creating a receipt for a specific invoice.
    """
    # Get the invoice instance
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        form = InvoicePaymentForm(request.POST)
        if form.is_valid():
            payment_amount = form.cleaned_data['amount_paid']
            payment_mode = form.cleaned_data['payment_mode']
            notes = form.cleaned_data.get('notes', '')

            # Validate payment amount
            if payment_amount > invoice.grand_total:
                form.add_error('amount_paid', "Payment amount cannot exceed the invoice's grand total.")
            elif payment_amount > invoice.amount_due:
                form.add_error('amount_paid', "Payment amount cannot exceed the remaining amount due.")
            else:
                with transaction.atomic():  # Ensure atomicity for the process
                    # Update the invoice's payment details
                    invoice.amount_paid += payment_amount
                    invoice.amount_due = max(invoice.grand_total - invoice.amount_paid, 0)

                    # Update the invoice status based on payment progress
                    if invoice.amount_paid == invoice.grand_total:
                        invoice.status = 'Payment Completed'
                    elif invoice.amount_paid > 0:
                        invoice.status = 'Payment Ongoing'
                    else:
                        invoice.status = 'Unpaid'

                    invoice.save()

                    # Create a receipt for the payment
                    receipt = Receipt.objects.create(
                        invoice=invoice,
                        amount_paid=payment_amount,
                        payment_method=payment_mode,
                        notes=notes,
                    )

                messages.success(request, f"Payment added successfully! Receipt ID: {receipt.receipt_id}")
                return redirect('invoices')
        else:
            messages.error(request, "Error adding payment. Please check the form.")
    else:
        form = InvoicePaymentForm()

    view_context = {
        'invoice': invoice,
        'form': form,
    }
    
    context = TemplateLayout.init(request, view_context)
    
    return render(request, 'makePayment.html', context)



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
