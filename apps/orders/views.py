from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .models import Bank, BankDeposit, Check, InvoiceAuditLog, InvoiceDocument, MomoInfo, PaymentSchedule, PurchaseOrder, PurchaseOrderAuditLog, PurchaseOrderDocument, PurchaseOrderItem, ReturnInvoice, ReturnInvoiceDocument, ReturnInvoiceOrderItem, ReturnInvoicePayment, ReturnOrderItem, ReturnPaymentSchedule, ReturnPurchaseOrderDocument, ReturnReceipt, TemporaryStock, InvoiceOrderItem, Invoice, InvoicePayment, Receipt
from apps.stock.models import Stock
from django.contrib import messages
from .forms import BankDepositForm, BankForm, CheckForm, InvoicerDocumentForm, MomoInfoForm, PaymentScheduleForm, PurchaseOrderDocumentForm, PurchaseOrderForm, PurchaseOrderItemForm, InvoicePaymentForm, PurchaseOrderTaxForm, ReturnInvoiceDocumentForm, ReturnInvoicePaymentForm, ReturnOrderItemForm, ReturnPurchaseOrderDocumentForm
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
from django.utils.translation import gettext_lazy as _
from django.forms import formset_factory
from datetime import datetime
from num2words import num2words




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


from itertools import chain
from django.db.models import Value

from django.db.models import F, ExpressionWrapper, DecimalField

@login_required
def order_list(request):
    search_query = request.GET.get("search_query", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status_filter = request.GET.get("status")
    branch_id = request.GET.get("branch")
    selected_month = request.GET.get("month")
    sales_rep_id = request.GET.get("sales_rep")  # New filter for sales rep

    branches = Branch.objects.all()
    sales_reps = Worker.objects.filter(role="Sales Rep").order_by("user__first_name", "user__last_name")
    user = request.user
    is_accountant_or_superuser = user.worker_profile.role == "Accountant" or user.is_superuser

    # Fetch purchase orders based on the user's role
    if is_accountant_or_superuser:
        purchase_orders = PurchaseOrder.objects.all()
        return_orders = ReturnPurchaseOrder.objects.all()
    else:
        user_branch = user.worker_profile.branch
        purchase_orders = PurchaseOrder.objects.filter(branch=user_branch)
        return_orders = ReturnPurchaseOrder.objects.filter(branch=user_branch)

    # Apply filters
    if start_date and end_date:
        purchase_orders = purchase_orders.filter(created_at__date__range=[start_date, end_date])
        return_orders = return_orders.filter(created_at__date__range=[start_date, end_date])

    if branch_id:
        purchase_orders = purchase_orders.filter(branch__id=branch_id)
        return_orders = return_orders.filter(branch__id=branch_id)

    if selected_month:
        purchase_orders = purchase_orders.filter(created_at__month=selected_month)
        return_orders = return_orders.filter(created_at__month=selected_month)

    if status_filter:
        purchase_orders = purchase_orders.filter(status__iexact=status_filter)
        return_orders = return_orders.filter(status__iexact=status_filter)

    if sales_rep_id:
        purchase_orders = purchase_orders.filter(sales_rep__id=sales_rep_id)
        return_orders = return_orders.filter(sales_rep__id=sales_rep_id)

    if search_query:
        purchase_orders = purchase_orders.filter(
            Q(purchase_order_id__icontains=search_query) |
            Q(branch__branch_id__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(sales_rep__user__first_name__icontains=search_query) |
            Q(sales_rep__user__last_name__icontains=search_query) |
            Q(payment_method__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

        return_orders = return_orders.filter(
            Q(return_order_id__icontains=search_query) |
            Q(branch__branch_id__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(sales_rep__user__first_name__icontains=search_query) |
            Q(sales_rep__user__last_name__icontains=search_query) |
            Q(payment_method__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

    # Merge and sort orders
    orders = sorted(
        chain(purchase_orders, return_orders),
        key=lambda order: (order.status.lower() != "pending", -order.created_at.timestamp()),
    )

    # Compute total values for display
    total_grand_total = Decimal(0)
    total_new_total = Decimal(0)

    for order in orders:
        tax_rate = Decimal(order.tax_rate or 0)
        precompte = Decimal(order.precompte or 0)
        tva = Decimal(order.tva or 0)

        tax_amount = (order.grand_total * tax_rate) / Decimal(100)
        tva_amount = (order.grand_total * tva) / Decimal(100)
        precompte_amount = (order.grand_total * precompte) / Decimal(100)

        if hasattr(order, "is_special_customer") and order.is_special_customer:
            order.new_total = order.grand_total + tva_amount + precompte_amount
        else:
            order.new_total = order.grand_total + tva_amount + tax_amount + precompte_amount

        order.tax_amount = tax_amount
        order.tva_amount = tva_amount
        order.precompte_amount = precompte_amount

        total_grand_total += order.grand_total
        total_new_total += order.new_total

    # Paginate results
    paginator = Paginator(orders, 100)
    page_number = request.GET.get("page")
    paginated_orders = paginator.get_page(page_number)

    offset = (paginated_orders.number - 1) * paginator.per_page

    months = [
        {"id": "1", "name": "January"}, {"id": "2", "name": "February"}, {"id": "3", "name": "March"},
        {"id": "4", "name": "April"}, {"id": "5", "name": "May"}, {"id": "6", "name": "June"},
        {"id": "7", "name": "July"}, {"id": "8", "name": "August"}, {"id": "9", "name": "September"},
        {"id": "10", "name": "October"}, {"id": "11", "name": "November"}, {"id": "12", "name": "December"},
    ]

    view_context = {
        "orders": paginated_orders,
        "search_query": search_query,
        "start_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
        "branch_id": branch_id,
        "branches": branches,
        "sales_reps": sales_reps,  # Add sales reps to the context
        "sales_rep_id": sales_rep_id,  # Add the selected sales rep
        "offset": offset,
        "months": months,
        "selected_month": selected_month,
        "total_grand_total": total_grand_total,
        "total_new_total": total_new_total,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "orderList.html", context)





@login_required
def add_tax_to_order(request, order_id):
    user = request.user
    worker = getattr(user, 'worker_profile', None)

    # Check if the user has Accountant privileges or is a superuser
    is_accountant_or_superuser = user.is_superuser or (worker and worker.role == "Accountant")

    if not is_accountant_or_superuser:
        messages.error(request, _("You do not have permission to add tax to this order."))
        return redirect("order_details", order_id=order_id)

    # Try fetching the order as a PurchaseOrder first
    order = None
    order_type = None

    if user.is_superuser:
        order = PurchaseOrder.objects.filter(id=order_id).first()
        if not order:
            order = ReturnPurchaseOrder.objects.filter(id=order_id).first()
            order_type = "return_purchase_order"
        else:
            order_type = "purchase_order"
    else:
        order = PurchaseOrder.objects.filter(id=order_id, branch=worker.branch).first()
        if not order:
            order = ReturnPurchaseOrder.objects.filter(id=order_id, branch=worker.branch).first()
            order_type = "return_purchase_order"
        else:
            order_type = "purchase_order"

    if not order:
        messages.error(request, _("No valid order found."))
        return redirect("order_details", order_id=order_id)

    if request.method == "POST":
        try:
            # Extract tax values from the form
            tax_rate = float(request.POST.get("tax_rate", 0.0))
            precompte = float(request.POST.get("precompte", 0.0))
            tva = float(request.POST.get("tva", 0.0))
            is_special_customer = request.POST.get("is_special_customer") == "on"

            # Get the correct tax choices based on order type
            if order_type == "return_purchase_order":
                valid_tax_rates = [choice[0] for choice in ReturnPurchaseOrder.TAX_RATE_CHOICES]
                valid_precomptes = [choice[0] for choice in ReturnPurchaseOrder.PRECOMPTE_CHOICES]
                valid_tvas = [choice[0] for choice in ReturnPurchaseOrder.TVA_CHOICES]
            else:
                valid_tax_rates = [choice[0] for choice in PurchaseOrder.TAX_RATE_CHOICES]
                valid_precomptes = [choice[0] for choice in PurchaseOrder.PRECOMPTE_CHOICES]
                valid_tvas = [choice[0] for choice in PurchaseOrder.TVA_CHOICES]

            # Validate tax values
            if tax_rate not in valid_tax_rates:
                messages.error(request, _("Invalid tax rate selected."))
                return redirect("order_details", order_id=order_id)
            if precompte not in valid_precomptes:
                messages.error(request, _("Invalid precompte selected."))
                return redirect("order_details", order_id=order_id)
            if tva not in valid_tvas:
                messages.error(request, _("Invalid TVA selected."))
                return redirect("order_details", order_id=order_id)

            # Update the order's tax details
            with transaction.atomic():
                order.tax_rate = tax_rate
                order.precompte = precompte
                order.tva = tva
                order.is_special_customer = is_special_customer
                order.notes = f"[Tax Update]: Tax values updated ({timezone.now().strftime('%Y-%m-%d %H:%M:%S')})"
                order.save()

                # Log the tax update action
                if worker:
                    PurchaseOrderAuditLog.objects.create(
                        user=worker,
                        action="update_tax",
                        order=order.id,
                        branch=worker.branch.branch_name,
                        details=f"Tax values updated: Tax Rate={tax_rate}, Precompte={precompte}, TVA={tva}, Special Customer={is_special_customer}",
                    )

            messages.success(request, _("Tax values and special customer status updated successfully."))
        except ValueError:
            messages.error(request, _("Invalid tax values provided. Please enter numeric values."))
        except Exception as e:
            messages.error(request, f"An error occurred while updating tax values: {str(e)}")

        return redirect("order_details", order_id=order.id)

    return redirect("order_details", order_id=order.id)





@login_required
def upload_purchase_order_document(request, order_id):
    """
    Handles document uploads for both Purchase Orders and Return Purchase Orders.
    Determines the type based on whether the order exists in PurchaseOrder or ReturnPurchaseOrder.
    """

    # Get the current worker profile from the logged-in user
    try:
        worker = request.user.worker_profile  # If using OneToOneField in Worker model
    except AttributeError:
        messages.error(request, "You are not assigned as a worker in the system.")
        return redirect('dashboard')  # Redirect to an appropriate page

    # Determine if it's a normal Purchase Order or a Return Purchase Order
    order = PurchaseOrder.objects.filter(id=order_id).first()
    is_return = False

    if not order:
        order = get_object_or_404(ReturnPurchaseOrder, id=order_id)
        is_return = True

    # Select the correct model and form
    if is_return:
        documents = ReturnPurchaseOrderDocument.objects.filter(return_purchase_order=order)
        form_class = ReturnPurchaseOrderDocumentForm
        model_class = ReturnPurchaseOrderDocument
    else:
        documents = PurchaseOrderDocument.objects.filter(purchase_order=order)
        form_class = PurchaseOrderDocumentForm
        model_class = PurchaseOrderDocument

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            new_document_type = form.cleaned_data['document_type']

            # Prevent duplicate document types
            if model_class.objects.filter(
                **({'return_purchase_order': order} if is_return else {'purchase_order': order}),
                document_type=new_document_type
            ).exists():
                messages.warning(request, f"A document of type '{new_document_type}' has already been uploaded.")
            else:
                document = form.save(commit=False)
                if is_return:
                    document.return_purchase_order = order
                else:
                    document.purchase_order = order

                # Assign the worker who uploaded the document
                document.uploaded_by = worker
                document.save()

                messages.success(request, "Document uploaded successfully.")
                return redirect('upload_purchase_order_document', order_id=order.id)

        else:
            messages.error(request, "Error uploading document. Please check the form.")

    else:
        form = form_class()

    context = TemplateLayout.init(request, {
        'form': form,
        'order': order,
        'documents': documents,
        'is_return': is_return,
    })

    return render(request, "upload_documents.html", context)



@login_required
def edit_document(request, document_id):
    """
    Handles editing of both Purchase Order and Return Purchase Order documents.
    """

    # Check if the document belongs to a normal or return purchase order
    document = PurchaseOrderDocument.objects.filter(id=document_id).first()
    is_return = False

    if not document:
        document = get_object_or_404(ReturnPurchaseOrderDocument, id=document_id)
        is_return = True

    order_id = document.return_purchase_order.id if is_return else document.purchase_order.id

    # Select the correct form
    form_class = ReturnPurchaseOrderDocumentForm if is_return else PurchaseOrderDocumentForm

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            return redirect('upload_purchase_order_document', order_id=order_id)

        else:
            messages.error(request, "Error updating document.")

    else:
        form = form_class(instance=document)

    context = TemplateLayout.init(request, {
        'form': form,
        'document': document,
        'is_return': is_return,
        'editing': True,
    })

    return render(request, "upload_documents.html", context)


@login_required
def delete_document(request, document_id):
    """
    Handles document deletion for both Purchase Orders and Return Purchase Orders.
    """

    document = PurchaseOrderDocument.objects.filter(id=document_id).first()
    is_return = False

    if not document:
        document = get_object_or_404(ReturnPurchaseOrderDocument, id=document_id)
        is_return = True

    order_id = document.return_purchase_order.id if is_return else document.purchase_order.id

    document.delete()
    messages.success(request, "Document deleted successfully.")
    return redirect('upload_purchase_order_document', order_id=order_id)






@login_required
def upload_invoice_document(request, invoice_id):
    """
    Handles document uploads for both Invoices and Return Invoices.
    Determines the type based on whether the invoice exists in Invoice or ReturnInvoice.
    """

    # Get the current worker profile from the logged-in user
    try:
        worker = request.user.worker_profile  # If using OneToOneField in Worker model
    except AttributeError:
        messages.error(request, "You are not assigned as a worker in the system.")
        return redirect('dashboard')  # Redirect to an appropriate page

    # Determine if it's a normal Invoice or a Return Invoice
    invoice = Invoice.objects.filter(id=invoice_id).first()
    is_return = False

    if not invoice:
        invoice = get_object_or_404(ReturnInvoice, id=invoice_id)
        is_return = True

    # Select the correct model and form
    if is_return:
        documents = ReturnInvoiceDocument.objects.filter(return_invoice=invoice)
        form_class = ReturnInvoiceDocumentForm
        model_class = ReturnInvoiceDocument
    else:
        documents = InvoiceDocument.objects.filter(invoice=invoice)
        form_class = InvoicerDocumentForm
        model_class = InvoiceDocument

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            new_document_type = form.cleaned_data['document_type']

            # Prevent duplicate document types
            if model_class.objects.filter(**({'return_invoice': invoice} if is_return else {'invoice': invoice}), document_type=new_document_type).exists():
                messages.warning(request, f"A document of type '{new_document_type}' has already been uploaded.")
            else:
                document = form.save(commit=False)
                if is_return:
                    document.return_invoice = invoice
                else:
                    document.invoice = invoice

                # Assign the worker who uploaded the document
                document.uploaded_by = worker
                document.save()
                messages.success(request, "Document uploaded successfully.")
                return redirect('upload_invoice_document', invoice_id=invoice.id)

        else:
            messages.error(request, "Error uploading document. Please check the form.")

    else:
        form = form_class()

    context = TemplateLayout.init(request, {
        'form': form,
        'invoice': invoice,
        'documents': documents,
        'is_return': is_return,
    })

    return render(request, "upload_invoice_documents.html", context)


@login_required
def edit_invoice_document(request, document_id):
    """
    Handles editing of both Invoice and Return Invoice documents.
    """

    # Check if the document belongs to a normal or return invoice
    document = InvoiceDocument.objects.filter(id=document_id).first()
    is_return = False

    if not document:
        document = get_object_or_404(ReturnInvoiceDocument, id=document_id)
        is_return = True

    invoice_id = document.return_invoice.id if is_return else document.invoice.id

    # Select the correct form
    form_class = ReturnInvoiceDocumentForm if is_return else InvoicerDocumentForm

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            return redirect('upload_invoice_document', invoice_id=invoice_id)

        else:
            messages.error(request, "Error updating document.")

    else:
        form = form_class(instance=document)

    context = TemplateLayout.init(request, {
        'form': form,
        'document': document,
        'is_return': is_return,
        'editing': True,
    })

    return render(request, "upload_invoice_documents.html", context)


@login_required
def delete_invoice_document(request, document_id):
    """
    Handles document deletion for both Invoices and Return Invoices.
    """

    document = InvoiceDocument.objects.filter(id=document_id).first()
    is_return = False

    if not document:
        document = get_object_or_404(ReturnInvoiceDocument, id=document_id)
        is_return = True

    invoice_id = document.return_invoice.id if is_return else document.invoice.id

    document.delete()
    messages.success(request, "Document deleted successfully.")
    return redirect('upload_invoice_document', invoice_id=invoice_id)




@login_required
def PurchaseOrderAuditLogView(request):
    logs = PurchaseOrderAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "order_logs.html", context)

@login_required
def InvoiceAuditLogView(request):
    logs = InvoiceAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "invoice_logs.html", context)


from django.db.models import Q, Case, When, Value
from itertools import chain
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Invoice, ReturnInvoice, Branch

@login_required
def invoice_list(request):
    search_query = request.GET.get("search_query", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status_filter = request.GET.get("status")
    branch_id = request.GET.get("branch")
    selected_month = request.GET.get("month")
    sales_rep_id = request.GET.get("sales_rep")  # New: Get sales rep filter from request

    branches = Branch.objects.all()
    sales_reps = Worker.objects.filter(role="Sales Rep").order_by("user__first_name", "user__last_name")
    user = request.user
    is_accountant_or_superuser = user.worker_profile.role == "Accountant" or user.is_superuser

    return_payment_schedules = set(ReturnPaymentSchedule.objects.values_list("return_purchase_order_id", flat=True))

    if is_accountant_or_superuser:
        invoices = Invoice.objects.select_related("purchase_order")
        return_invoices = ReturnInvoice.objects.select_related("return_purchase_order")
    else:
        user_branch = user.worker_profile.branch
        invoices = Invoice.objects.filter(branch=user_branch).select_related("purchase_order")
        return_invoices = ReturnInvoice.objects.filter(branch=user_branch).select_related("return_purchase_order")

    if start_date and end_date:
        invoices = invoices.filter(created_at__date__range=[start_date, end_date])
        return_invoices = return_invoices.filter(created_at__date__range=[start_date, end_date])

    if branch_id:
        invoices = invoices.filter(branch__id=branch_id)
        return_invoices = return_invoices.filter(branch__id=branch_id)

    if selected_month:
        invoices = invoices.filter(created_at__month=selected_month)
        return_invoices = return_invoices.filter(created_at__month=selected_month)

    if status_filter:
        invoices = invoices.filter(status__iexact=status_filter)
        return_invoices = return_invoices.filter(status__iexact=status_filter)

    if sales_rep_id:
        invoices = invoices.filter(sales_rep__id=sales_rep_id)
        return_invoices = return_invoices.filter(sales_rep__id=sales_rep_id)

    if search_query:
        invoices = invoices.filter(
            Q(invoice_id__icontains=search_query) |
            Q(branch__branch_id__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(sales_rep__user__first_name__icontains=search_query) |
            Q(sales_rep__user__last_name__icontains=search_query) |
            Q(payment_method__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

        return_invoices = return_invoices.filter(
            Q(return_invoice_id__icontains=search_query) |
            Q(branch__branch_id__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(sales_rep__user__first_name__icontains=search_query) |
            Q(sales_rep__user__last_name__icontains=search_query) |
            Q(payment_method__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(created_by__user__first_name__icontains=search_query) |
            Q(created_by__user__last_name__icontains=search_query)
        )

    all_invoices = sorted(
        chain(invoices, return_invoices),
        key=lambda invoice: (invoice.status.lower() != "unpaid", -invoice.created_at.timestamp()),
    )

        # Initialize total variables
    total_tht = Decimal(0)  # Total before taxes
    total_ttc = Decimal(0)  # Total including all taxes
    total_paid = Decimal(0)  # Total amount paid
    total_due = Decimal(0)  # Total due

    # Compute tax amounts based on related Purchase Orders or Return Purchase Orders
    for invoice in all_invoices:
        if hasattr(invoice, "purchase_order") and invoice.purchase_order:
            tax_rate = Decimal(invoice.purchase_order.tax_rate or 0)
            tva = Decimal(invoice.purchase_order.tva or 0)
            precompte = Decimal(invoice.purchase_order.precompte or 0)
        elif hasattr(invoice, "return_purchase_order") and invoice.return_purchase_order:
            tax_rate = Decimal(invoice.return_purchase_order.tax_rate or 0)
            tva = Decimal(invoice.return_purchase_order.tva or 0)
            precompte = Decimal(invoice.return_purchase_order.precompte or 0)
        else:
            tax_rate = tva = precompte = Decimal(0)

        tax_amount = (invoice.grand_total * tax_rate) / Decimal(100)
        tva_amount = (invoice.grand_total * tva) / Decimal(100)
        precompte_amount = (invoice.grand_total * precompte) / Decimal(100)

        # Adjust total based on invoice type
        if hasattr(invoice, "is_special_customer") and invoice.is_special_customer:
            invoice.new_total = invoice.grand_total + tva_amount + precompte_amount
        else:
            invoice.new_total = invoice.grand_total + tva_amount + tax_amount + precompte_amount

        # Attach computed values for display
        invoice.tax_amount = tax_amount
        invoice.tva_amount = tva_amount
        invoice.precompte_amount = precompte_amount

        # Compute totals
        total_tht += invoice.grand_total  # Before tax
        total_ttc += invoice.new_total  # Including all taxes
        total_paid += invoice.amount_paid if hasattr(invoice, "amount_paid") else Decimal(0)

        # Correct total_due calculation: total_due = new_total - paid amount
        total_due += invoice.new_total - (invoice.amount_paid if hasattr(invoice, "amount_paid") else Decimal(0))

    paginator = Paginator(all_invoices, 100)
    page_number = request.GET.get("page")
    paginated_invoices = paginator.get_page(page_number)
    offset = (paginated_invoices.number - 1) * paginator.per_page

    months = [{"id": str(i), "name": month} for i, month in enumerate([
        "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], start=1)]

    view_context = {
        "invoices": paginated_invoices,
        "search_query": search_query,
        "start_date": start_date,
        "return_payment_schedules": return_payment_schedules,
        "end_date": end_date,
        "status_filter": status_filter,
        "branch_id": branch_id,
        "branches": branches,
        "offset": offset,
        "months": months,
        "selected_month": selected_month,
        "sales_rep_id": sales_rep_id,  # Pass selected sales rep to template
        "sales_reps": sales_reps,  # Pass all sales reps for selection in the UI
        "total_tht": total_tht,
        "total_ttc": total_ttc,
        "total_paid": total_paid,
        "total_due": total_due,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, "invoiceList.html", context)




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from .models import Invoice, PurchaseOrder, PurchaseOrderItem, InvoiceOrderItem, Stock, ReturnOrderItem, PurchaseOrderAuditLog
from .forms import ReturnOrderItemForm

@login_required
def return_items(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    user_branch = request.user.worker_profile.branch

    # Ensure session exists
    if "return_items" not in request.session:
        request.session["return_items"] = []

    item_form = ReturnOrderItemForm(invoice_id=invoice_id)

    if request.method == "POST":
        action = request.POST.get("action", "")
        return_items = request.session.get("return_items", [])

        if action == "add_item":
            item_form = ReturnOrderItemForm(request.POST, invoice_id=invoice_id)
            if item_form.is_valid():
                invoice_order_item = item_form.cleaned_data["invoice_order_item"]
                quantity_returned = item_form.cleaned_data["quantity_returned"]
                reason_for_return = item_form.cleaned_data["reason_for_return"]

                if quantity_returned > invoice_order_item.quantity:
                    messages.error(
                        request,
                        f"Cannot return more than {invoice_order_item.quantity} of {invoice_order_item.stock.product.product_code}."
                    )
                else:
                    return_items.append({
                        "stock_id": invoice_order_item.stock.id,
                        "stock_name": str(invoice_order_item.stock.product.product_code),
                        "quantity_returned": quantity_returned,
                        "reason_for_return": reason_for_return,
                        "invoice_order_item_id": invoice_order_item.id,
                    })
                    request.session["return_items"] = return_items
                    request.session.modified = True
                    messages.success(request, f"Added {quantity_returned} of {invoice_order_item.stock.product.product_code} to return list.")

        elif action == "remove_item":
            try:
                item_index = int(request.POST.get("item_index", -1))
                if 0 <= item_index < len(return_items):
                    removed_item = return_items.pop(item_index)
                    request.session["return_items"] = return_items
                    request.session.modified = True
                    messages.success(request, f"Removed {removed_item['stock_name']} from return list.")
                else:
                    messages.error(request, "Invalid item index provided.")
            except ValueError:
                messages.error(request, "Invalid item index provided.")

        elif action == "submit_return":
            if return_items:
                try:
                    with transaction.atomic():
                        original_po = invoice.purchase_order

                        # Create a new Purchase Order for the return
                        revised_po = PurchaseOrder.objects.create(
                            branch=original_po.branch,
                            customer=original_po.customer,
                            sales_rep=original_po.sales_rep,
                            payment_method=original_po.payment_method,
                            payment_mode=original_po.payment_mode,
                            created_at=timezone.now(),
                            created_by=request.user.worker_profile,
                            status='Approved',
                            grand_total=Decimal('0.00'),
                            notes=f"Revised due to return. Original PO: {original_po.purchase_order_id}",
                            momo_account=original_po.momo_account,
                            check_account=original_po.check_account,
                            bank_deposit_account=original_po.bank_deposit_account,
                            old_purchase_order_id=original_po.purchase_order_id  # Store the original PO ID
                        )

                        # Set the new Purchase Order ID to be "RET-" + the old PO ID
                        revised_po.purchase_order_id = f"RET-{original_po.purchase_order_id}"
                        revised_po.save()

                        revised_total = Decimal('0.00')

                        for orig_item in original_po.items.all():
                            return_item = next((ri for ri in return_items if ri["invoice_order_item_id"] == orig_item.id), None)
                            if return_item:
                                remaining_qty = orig_item.quantity - Decimal(str(return_item["quantity_returned"]))
                                if remaining_qty > 0:
                                    PurchaseOrderItem.objects.create(
                                        purchase_order=revised_po,
                                        stock=orig_item.stock,
                                        quantity=remaining_qty,
                                        temp_price=orig_item.temp_price,
                                    )
                                    revised_total += remaining_qty * orig_item.temp_price
                            else:
                                PurchaseOrderItem.objects.create(
                                    purchase_order=revised_po,
                                    stock=orig_item.stock,
                                    quantity=orig_item.quantity,
                                    temp_price=orig_item.temp_price,
                                )
                                revised_total += orig_item.quantity * orig_item.temp_price

                        revised_po.grand_total = revised_total
                        revised_po.save()

                        # Create a new Invoice for the return
                        revised_invoice = Invoice.objects.create(
                            branch=invoice.branch,
                            customer=invoice.customer,
                            sales_rep=invoice.sales_rep,
                            payment_method=invoice.payment_method,
                            created_at=timezone.now(),
                            created_by=request.user.worker_profile,
                            purchase_order=revised_po,
                            grand_total=revised_total,
                            amount_paid=Decimal('0.00'),
                            amount_due=revised_total,
                            status='Unpaid',
                            old_invoice_id=invoice.invoice_id  # Store the original Invoice ID
                        )

                        # Set the new Invoice ID to be "RET-" + the old Invoice ID
                        revised_invoice.invoice_id = f"RET-{invoice.invoice_id}"
                        revised_invoice.save()

                        for orig_item in invoice.items.all():
                            return_item = next((ri for ri in return_items if ri["invoice_order_item_id"] == orig_item.id), None)
                            if return_item:
                                remaining_qty = orig_item.quantity - Decimal(str(return_item["quantity_returned"]))
                                if remaining_qty > 0:
                                    InvoiceOrderItem.objects.create(
                                        invoice_order=revised_invoice,
                                        stock=orig_item.stock,
                                        quantity=remaining_qty,
                                        price=orig_item.price,
                                    )
                            else:
                                InvoiceOrderItem.objects.create(
                                    invoice_order=revised_invoice,
                                    stock=orig_item.stock,
                                    quantity=orig_item.quantity,
                                    price=orig_item.price,
                                )

                        # Update the stock quantities and create return order items
                        for return_item in return_items:
                            stock = get_object_or_404(Stock, id=return_item["stock_id"])
                            stock.total_sold -= Decimal(str(return_item["quantity_returned"]))
                            stock.save()

                            ReturnOrderItem.objects.create(
                                invoice_order_item=get_object_or_404(InvoiceOrderItem, id=return_item["invoice_order_item_id"]),
                                quantity_returned=Decimal(str(return_item["quantity_returned"])) ,
                                reason_for_return=return_item["reason_for_return"],
                                created_by=request.user.worker_profile,
                            )

                            PurchaseOrderAuditLog.objects.create(
                                user=request.user.worker_profile,
                                action="return",
                                order=invoice.invoice_id,
                                branch=user_branch.branch_name,
                                details=f"Returned {return_item['quantity_returned']} of {return_item['stock_name']}. Reason: {return_item['reason_for_return']}"
                            )

                        # Clear the session and finish the process
                        request.session["return_items"] = []
                        request.session.modified = True
                        messages.success(request, "Returns processed successfully and revised records created.")
                        return redirect("invoices")

                except Exception as e:
                    messages.error(request, f"Error processing returns: {e}")
            else:
                messages.error(request, "No items in the return list.")

    view_context = {"item_form": item_form, "return_items": request.session["return_items"]}
    context = TemplateLayout.init(request, view_context)

    return render(request, "return_items.html", context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import (
    Invoice, InvoiceOrderItem, ReturnInvoice, ReturnInvoiceOrderItem,
    PurchaseOrderItem, ReturnPurchaseOrder, ReturnPurchaseOrderItem, Stock
)
from .forms import ReturnOrderItemForm

from .models import ReturnItemTemp

def to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal("0.0")

@login_required
@transaction.atomic
def process_return(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    user = request.user

    # Get temporary return items for the current user
    temp_items = ReturnItemTemp.objects.filter(user=user)

    item_form = ReturnOrderItemForm(invoice_id=invoice_id)

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "add_item":
            item_form = ReturnOrderItemForm(request.POST, invoice_id=invoice_id)
            if item_form.is_valid():
                invoice_order_item = item_form.cleaned_data["invoice_order_item"]
                try:
                    quantity_returned = to_decimal(item_form.cleaned_data["quantity_returned"])
                except (InvalidOperation, TypeError):
                    messages.error(request, "Invalid quantity entered.")
                    return redirect("process_return", invoice_id=invoice_id)

                reason_for_return = item_form.cleaned_data["reason_for_return"]

                # Compare using forced Decimal conversion
                if quantity_returned > to_decimal(invoice_order_item.quantity):
                    messages.error(
                        request,
                        f"Cannot return more than {invoice_order_item.quantity} of {invoice_order_item.stock.product.product_code}."
                    )
                else:
                    # Create a temporary record for this return item.
                    ReturnItemTemp.objects.create(
                        user=user,
                        invoice_order_item=invoice_order_item,
                        quantity_returned=quantity_returned,
                        reason_for_return=reason_for_return,
                    )
                    messages.success(
                        request,
                        f"Added {quantity_returned} of {invoice_order_item.stock.product.product_code} to return list."
                    )
                    return redirect("process_return", invoice_id=invoice_id)

        elif action == "remove_item":
            temp_id_str = request.POST.get("temp_item_id")
            if not temp_id_str:
                messages.error(request, "No temporary item id provided for removal.")
                return redirect("process_return", invoice_id=invoice_id)
            
            try:
                temp_id = int(temp_id_str)
                temp_item = ReturnItemTemp.objects.get(id=temp_id, user=user)
                temp_item.delete()
                messages.success(request, "Removed item from return list.")
            except (ReturnItemTemp.DoesNotExist, ValueError):
                messages.error(request, "Invalid item provided for removal.")



        elif action == "submit_return":
            temp_items = ReturnItemTemp.objects.filter(user=user)
            if not temp_items.exists():
                messages.error(request, "No items added for return.")
                return redirect("process_return", invoice_id=invoice_id)

            try:
                with transaction.atomic():
                    return_invoice_id = f"RET-{invoice.invoice_id}"
                    new_grand_total = Decimal("0.0")
                    processed_items = []

                    # Process each temporary item record.
                    for temp in temp_items:
                        invoice_order_item = temp.invoice_order_item
                        # Force both operands to Decimal using our helper
                        old_quantity = to_decimal(invoice_order_item.quantity)
                        quantity_returned = to_decimal(temp.quantity_returned)
                        remaining_quantity = Decimal(str(invoice_order_item.quantity)) - Decimal(str(temp.quantity_returned))  # Both are Decimal now
                        price = to_decimal(invoice_order_item.price)
                        new_grand_total += remaining_quantity * price

                        processed_items.append({
                            "stock_id": invoice_order_item.stock.id,
                            "invoice_order_item_id": invoice_order_item.id,
                            "remaining_quantity": remaining_quantity,  # Decimal
                            "quantity_returned": quantity_returned,      # Decimal
                            "price": price,                              # Decimal
                            "reason_for_return": temp.reason_for_return,
                        })

                    # Create the ReturnPurchaseOrder
                    return_purchase_order = ReturnPurchaseOrder.objects.create(
                        return_order_id=f"RET-{invoice.purchase_order.purchase_order_id}",
                        original_purchase_order=invoice.purchase_order,
                        branch=invoice.branch,
                        customer=invoice.purchase_order.customer,
                        sales_rep=invoice.purchase_order.sales_rep,
                        created_by=request.user.worker_profile,
                        grand_total=new_grand_total,
                        status='Approved',
                        payment_method=invoice.purchase_order.payment_method,
                        payment_mode=invoice.purchase_order.payment_mode,
                        tax_rate=invoice.purchase_order.tax_rate,
                        precompte=invoice.purchase_order.precompte,
                        tva=invoice.purchase_order.tva,
                        is_special_customer=invoice.purchase_order.is_special_customer,
                        notes=f"Return Order for Invoice {invoice.invoice_id}"
                    )

                    # Create the ReturnInvoice and link it
                    return_invoice = ReturnInvoice.objects.create(
                        return_invoice_id=return_invoice_id,
                        original_invoice=invoice,
                        branch=invoice.branch,
                        created_by=request.user.worker_profile,
                        customer=invoice.customer,
                        sales_rep=invoice.sales_rep,
                        return_purchase_order=return_purchase_order,
                        grand_total=new_grand_total,
                        amount_due=new_grand_total,
                        status='UnPaid',
                    )

                    # Process each return item: create order items and update stock.
                    for item in processed_items:
                        stock = get_object_or_404(Stock, id=item["stock_id"])
                        invoice_order_item = get_object_or_404(InvoiceOrderItem, id=item["invoice_order_item_id"])

                        ReturnPurchaseOrderItem.objects.create(
                            return_purchase_order=return_purchase_order,
                            stock=stock,
                            quantity=int(item["remaining_quantity"]),
                            return_reason=item["reason_for_return"],
                        )

                        ReturnInvoiceOrderItem.objects.create(
                            return_invoice=return_invoice,
                            stock=stock,
                            quantity=int(item["remaining_quantity"]),
                            temp_price=item["price"],
                        )

                        # Increase warehouse stock by the returned quantity.
                        stock.total_stock += int(item["quantity_returned"])
                        stock.save()

                        # Update the invoice order item with the new remaining quantity.
                        invoice_order_item.quantity = int(item["remaining_quantity"])
                        invoice_order_item.save()

                    # Delete all temporary items once processed.
                    temp_items.delete()

                    messages.success(request, "Return processed successfully.")
                    return redirect("invoices")

            except Exception as e:
                messages.error(request, f"An error occurred while processing the return: {str(e)}")
                return redirect("process_return", invoice_id=invoice_id)

    view_context = {
        "invoice": invoice,
        "item_form": item_form,
        "temp_items": temp_items,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "return_items.html", context)



# @login_required
# def return_items(request, invoice_id):
#     invoice = get_object_or_404(Invoice, id=invoice_id)

#     if request.method == 'POST':
#         form = ReturnOrderItemForm(request.POST, invoice_id=invoice_id)
#         if form.is_valid():
#             item = form.cleaned_data['return_item']
#             return_quantity = form.cleaned_data['return_quantity']
#             reason_for_return = form.cleaned_data['reason_for_return']

#             if return_quantity > item.quantity:
#                 messages.error(request, f"Cannot return more than {item.quantity} of {item.stock.product.product_code}.")
#                 return redirect('return_items', invoice_id=invoice_id)

#             try:
#                 with transaction.atomic():
#                     # Update stock
#                     stock = item.stock
#                     stock.quantity += return_quantity
#                     stock.save()

#                     # Create return record
#                     ReturnOrderItem.objects.create(
#                         invoice_order_item=item,
#                         quantity_returned=return_quantity,
#                         reason_for_return=reason_for_return,
#                         created_by=request.user.worker_profile if hasattr(request.user, 'worker_profile') else None
#                     )

#                     messages.success(request, "Item returned successfully.")
#                     return redirect('invoice_details', invoice_id=invoice.id)
#             except Exception as e:
#                 messages.error(request, f"An error occurred: {str(e)}")
#                 return redirect('return_items', invoice_id=invoice_id)

#     else:
#         form = ReturnOrderItemForm(invoice_id=invoice_id)

#     view_context = {'form': form, 'invoice': invoice}

#     context = TemplateLayout.init(request, view_context)

#     return render(request, 'return_items.html', context)






from django.shortcuts import render, get_object_or_404
from django.db.models import Case, When, F, FloatField, ExpressionWrapper
from decimal import Decimal
from .models import Invoice, ReturnInvoice, PurchaseOrder, PurchaseOrderItem, ReturnPurchaseOrder, ReturnPurchaseOrderItem, PaymentSchedule

@login_required
def invoice_doc_view(request, invoice_id):
    """
    View to generate the invoice document for a normal invoice or return invoice.
    """
    invoice = None
    is_return_invoice = False

    # Try fetching as a normal invoice first
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        # If not found, try fetching as a return invoice
        try:
            invoice = ReturnInvoice.objects.get(id=invoice_id)
            is_return_invoice = True
        except ReturnInvoice.DoesNotExist:
            messages.error(request, "Invoice not found.")
            return redirect("invoices")  # Redirect to the invoice list page

    # Initialize variables
    purchase_order = None
    return_purchase_order = None
    items = []
    subtotal = Decimal(0.0)
    grand_total = Decimal(0.0)
    tax_rate = Decimal(0.0)
    precompte = Decimal(0.0)
    tva = Decimal(0.0)
    payment_schedules = []
    return_payment_schedules = []  # Handle return payment schedules
    payment_mode_details = None

    if is_return_invoice:
        # Handle ReturnInvoice
        return_purchase_order = invoice.return_purchase_order

        if not return_purchase_order:
            messages.error(request, "Return Purchase Order not found for this Return Invoice.")
            return redirect("invoices")

        # Fetch items for ReturnInvoice
        items = ReturnPurchaseOrderItem.objects.filter(return_purchase_order=return_purchase_order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F("temp_price")),
                default=F("stock__product__unit_price"),
                output_field=FloatField(),
            ),
            total_price=ExpressionWrapper(F("quantity") * F("effective_price"), output_field=FloatField()),
        )

        subtotal = sum(item.total_price for item in items)
        grand_total = Decimal(return_purchase_order.grand_total)  # Fetch from return purchase order

        tax_rate = Decimal(return_purchase_order.tax_rate or 0)
        precompte = Decimal(return_purchase_order.precompte or 0)
        tva = Decimal(return_purchase_order.tva or 0)

        # Fetch return payment schedules
        return_payment_schedules = ReturnPaymentSchedule.objects.filter(return_purchase_order=return_purchase_order)

    else:
        # Handle regular Invoice
        purchase_order = invoice.purchase_order

        if not purchase_order:
            messages.error(request, "Purchase Order not found for this Invoice.")
            return redirect("invoices")

        # Fetch items for regular Invoice
        items = PurchaseOrderItem.objects.filter(purchase_order=purchase_order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F("temp_price")),
                default=F("stock__product__unit_price"),
                output_field=FloatField(),
            ),
            total_price=ExpressionWrapper(F("quantity") * F("effective_price"), output_field=FloatField()),
        )

        subtotal = sum(item.total_price for item in items)
        grand_total = Decimal(purchase_order.grand_total)  # Fetch from purchase order

        tax_rate = Decimal(purchase_order.tax_rate or 0)
        precompte = Decimal(purchase_order.precompte or 0)
        tva = Decimal(purchase_order.tva or 0)

        # Fetch payment schedules for regular invoices
        payment_schedules = PaymentSchedule.objects.filter(purchase_order=purchase_order)

        if purchase_order:
            if purchase_order.payment_mode == "Mobile Money":
                payment_mode_details = purchase_order.momo_account
            elif purchase_order.payment_mode == "Check":
                payment_mode_details = purchase_order.check_account
            elif purchase_order.payment_mode == "Bank Deposit":
                payment_mode_details = purchase_order.bank_deposit_account

    # Calculate tax amounts
    tax_amount = (grand_total * tax_rate) / Decimal(100)
    tva_amount = (grand_total * tva) / Decimal(100)
    precompte_amount = (grand_total * precompte) / Decimal(100)

    # Calculate the final total
    if purchase_order and purchase_order.is_special_customer:
        new_total = grand_total + tva_amount + precompte_amount  # Excluding tax_amount only for special customers
    else:
        new_total = grand_total + tva_amount + tax_amount + precompte_amount  # Including all taxes

    new_total_words = num2words(new_total, lang='en').capitalize()# Convert new_total to words


    view_context = {
        "invoice": invoice,
        "purchase_order": purchase_order,
        "return_purchase_order": return_purchase_order,
        "items": items,
        "payment_schedules": payment_schedules,
        "return_payment_schedules": return_payment_schedules,  # Added return payment schedules
        "payment_mode_details": payment_mode_details,
        "subtotal": subtotal,
        "grand_total": grand_total,
        "tax_rate": tax_rate,
        "precompte": precompte,
        "tva": tva,
        "tva_amount": tva_amount,
        "tax_amount": tax_amount,
        "precompte_amount": precompte_amount,
        "new_total": new_total,
        "new_total_words": new_total_words,  # Add the total amount in words
        "is_special_customer": purchase_order.is_special_customer if purchase_order else False,
        "is_return_invoice": is_return_invoice,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "invoice_facture.html", context)






@login_required
def receipt_doc_view(request, receipt_id):
    """
    View to get the details of a specific receipt (normal or return) and its associated invoice, including items.
    """
    # Try to get a normal receipt first
    receipt = Receipt.objects.filter(receipt_id=receipt_id).first()
    return_receipt = ReturnReceipt.objects.filter(receipt_id=receipt_id).first()

    if not receipt and not return_receipt:
        messages.error(request, "Receipt not found.")
        return redirect('invoice_list')

    # Determine whether it's a return receipt
    is_return_receipt = bool(return_receipt)
    receipt_instance = return_receipt if is_return_receipt else receipt
    invoice = return_receipt.return_invoice if is_return_receipt else receipt.invoice

    # Use the total_with_taxes directly from the invoice
    total_with_taxes = invoice.total_with_taxes

    # Get invoice items based on whether it's a normal or return invoice
    if is_return_receipt:
        # Fetch items from return invoice order items
        invoice_items = return_receipt.return_invoice.items.all()
    else:
        # Fetch items from regular invoice order items
        invoice_items = receipt.invoice.items.all()

    amount_paid_words = num2words(receipt.amount_paid, lang='en').capitalize()

    # Prepare the context for the template
    view_context = {
        "receipt": receipt_instance,
        "invoice": invoice,
        "amount_paid_words": amount_paid_words,
        "total_with_taxes": total_with_taxes,  # Directly use the total with taxes
        "invoice_items": invoice_items,  # Only display invoice items or return invoice items
        "is_return_receipt": is_return_receipt,  # Helps in template rendering
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'receipt.html', context)






@login_required
def picking_list_doc_view(request, purchase_order_id):
    """
    View to get the details of a specific receipt and its associated invoice.
    """
    order = get_object_or_404(PurchaseOrder, purchase_order_id=purchase_order_id)

    # Get the purchase order items if a purchase order exists
    order_items = PurchaseOrderItem.objects.filter(purchase_order=order).annotate(
        effective_price=Case(
            When(temp_price__isnull=False, then=F('temp_price')),
            default=F('stock__product__unit_price'),
            output_field=FloatField()
        ),
        total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
    )

    view_context = {
        "order": order,
        "order_items": order_items,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'picking_list.html', context)



@login_required
def payment_receipt_view(request, payment_id):
    """
    View to get the receipt associated with a specific payment.
    Redirects to the correct receipt page (normal or return).
    """
    # Try to get a normal invoice payment first
    payment = InvoicePayment.objects.filter(id=payment_id).first()
    return_payment = ReturnInvoicePayment.objects.filter(id=payment_id).first()

    if not payment and not return_payment:
        messages.error(request, _("Invalid payment reference."))
        return redirect('invoice_list')

    # Determine if it's a return invoice payment
    is_return_payment = bool(return_payment)
    payment_instance = return_payment if is_return_payment else payment

    # Fetch the correct receipt type
    if is_return_payment:
        receipt = ReturnReceipt.objects.filter(
            return_invoice=payment_instance.return_invoice,
            amount_paid=payment_instance.amount_paid
        ).first()
    else:
        receipt = Receipt.objects.filter(
            invoice=payment_instance.invoice,
            amount_paid=payment_instance.amount_paid
        ).first()

    # Redirect to the correct receipt page if found
    if receipt:
        return redirect('receipt_doc', receipt_id=receipt.receipt_id)

    messages.error(request, _("No receipt found for this payment."))
    return redirect('payment_history', invoice_id=payment_instance.invoice.id if not is_return_payment else payment_instance.return_invoice.id)




from django.http import Http404

@login_required
def order_details(request, order_id):
    user = request.user
    worker = user.worker_profile

    # Check if the user is a superuser or has "Accountant" privileges
    is_accountant_or_superuser = user.is_superuser or worker.role == "Accountant"

    # Determine if the order is a PurchaseOrder or ReturnPurchaseOrder
    try:
        # Try fetching the order as a PurchaseOrder
        if is_accountant_or_superuser:
            order = get_object_or_404(PurchaseOrder, id=order_id)
        else:
            order = get_object_or_404(PurchaseOrder, id=order_id, branch=worker.branch)

        # Fetch items for PurchaseOrder and annotate with effective_price and total_price
        order_items = PurchaseOrderItem.objects.filter(purchase_order=order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F('temp_price')),
                default=F('stock__product__unit_price'),
                output_field=FloatField()
            ),
            total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
        )
        order_type = "purchase_order"
    except Http404:
        # If not a PurchaseOrder, try fetching as a ReturnPurchaseOrder
        if is_accountant_or_superuser:
            order = get_object_or_404(ReturnPurchaseOrder, id=order_id)
        else:
            order = get_object_or_404(ReturnPurchaseOrder, id=order_id, branch=worker.branch)

        # Fetch items for ReturnPurchaseOrder and annotate with effective_price and total_price
        order_items = ReturnPurchaseOrderItem.objects.filter(return_purchase_order=order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F('temp_price')),
                default=F('stock__product__unit_price'),
                output_field=FloatField()
            ),
            total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
        )
        order_type = "return_purchase_order"

    # Calculate total quantity
    total_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    # Calculate total amount (before taxes) using the expression for total price
    total_price = order_items.aggregate(
        total_price=Sum(
            ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
        )
    )['total_price'] or Decimal(0)

    # Check if the order is from a special customer
    is_special_customer = order.is_special_customer  # Fetch from PurchaseOrder model

    # Convert tax fields to Decimal for precise calculations
    tax_rate = Decimal(order.tax_rate or 0) / 100 if not is_special_customer else Decimal(0)  # Exempt if special
    precompte = Decimal(order.precompte or 0) / 100
    tva = Decimal(order.tva or 0) / 100

    # Ensure that total_price is a Decimal (if it's float, convert it to Decimal)
    total_price_decimal = Decimal(total_price)

    # Calculate tax amounts
    tax_amount = total_price_decimal * tax_rate
    precompte_amount = total_price_decimal * precompte
    tva_amount = total_price_decimal * tva

    # Final total including applicable taxes
    total_with_taxes = total_price_decimal + tax_amount + precompte_amount + tva_amount

    # Fetch the worker's privileges
    worker_privileges = worker.privileges.values_list('name', flat=True)

    # Context for the template
    view_context = {
        "order": order,
        "order_items": order_items,
        "total_quantity": total_quantity,
        "worker_privileges": worker_privileges,
        "order_type": order_type,  # Pass the order type to the template
        "total_price": total_price_decimal,  # Total before taxes
        "total_with_taxes": total_with_taxes,  # Total after taxes
        "tax_details": {
            "is_special_customer": is_special_customer,
            "tax_rate": tax_rate * 100,  # Convert back to percentage for display
            "precompte": precompte * 100,
            "tva": tva * 100,
            "tax_amount": tax_amount,
            "precompte_amount": precompte_amount,
            "tva_amount": tva_amount,
        },
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
    View to display the payment history for a specific invoice (normal or return invoice).
    """
    # Determine whether it's a normal invoice or a return invoice
    invoice = Invoice.objects.filter(id=invoice_id).first()
    return_invoice = ReturnInvoice.objects.filter(id=invoice_id).first()

    if not invoice and not return_invoice:
        messages.error(request, _("Invalid invoice reference."))
        return redirect('invoice_list')

    # Determine the invoice type
    is_return_invoice = bool(return_invoice)
    invoice_instance = return_invoice if is_return_invoice else invoice

    # Fetch the correct payment history
    payment_history = (
        ReturnInvoicePayment.objects.filter(return_invoice=return_invoice).order_by('-payment_date')
        if is_return_invoice else
        InvoicePayment.objects.filter(invoice=invoice).order_by('-payment_date')
    )

    # Calculate payment percentages
    if invoice_instance.grand_total > 0:  # Avoid division by zero
        percentage_paid = (invoice_instance.amount_paid / invoice_instance.grand_total) * 100
        percentage_left = (invoice_instance.amount_due / invoice_instance.grand_total) * 100
    else:
        percentage_paid = 0
        percentage_left = 0

    # Pass context to the template
    context = TemplateLayout.init(
        request,
        {
            'invoice': invoice_instance,
            'payment_history': payment_history,
            'is_return_invoice': is_return_invoice,  # Helps differentiate in the template
            'percentage_paid': round(percentage_paid, 2),
            'percentage_left': round(percentage_left, 2),
        }
    )

    return render(request, 'paymentInvoiceHistory.html', context)



@login_required
def create_purchase_order(request):
    """
    Create a purchase order. Superusers can access all branches, while regular users are restricted to their branch.
    """
    # Determine if the user is a superuser or has a specific branch
    if request.user.is_superuser:
        user_is_superuser = True
        user_branch = None  # Superuser can access all branches
    else:
        user_is_superuser = False
        user_branch = request.user.worker_profile.branch  # Get the branch for the logged-in user

    if request.method == "POST":
        # Pass 'user_is_superuser' and 'user_branch' to the form
        po_form = PurchaseOrderForm(data=request.POST, user_is_superuser=user_is_superuser, user_branch=user_branch)

        if po_form.is_valid():
            created_at = po_form.cleaned_data["created_at"]
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')

            # Save form data to the session instead of creating the purchase order immediately
            request.session["purchase_order_details"] = {
                "created_at": created_at_str,
                "branch": po_form.cleaned_data["branch"].id if user_is_superuser else user_branch.id,
                "customer": po_form.cleaned_data["customer"].id,
                "sales_rep": po_form.cleaned_data["sales_rep"].id,
                "payment_method": po_form.cleaned_data["payment_method"],
                "payment_mode": po_form.cleaned_data["payment_mode"],
                "momo_account_details": po_form.cleaned_data["momo_account_details"].id if po_form.cleaned_data["momo_account_details"] else None,
                "check_account_details": po_form.cleaned_data["check_account_details"].id if po_form.cleaned_data["check_account_details"] else None,
                "bank_deposit_account_details": po_form.cleaned_data["bank_deposit_account_details"].id if po_form.cleaned_data["bank_deposit_account_details"] else None,
                "tax_rate": str(po_form.cleaned_data["tax_rate"]),  # Convert to string to store in session
                "precompte": str(po_form.cleaned_data["precompte"]),
                "tva": str(po_form.cleaned_data["tva"]),
                "is_special_customer": po_form.cleaned_data["is_special_customer"],  # Boolean field
            }

            # Redirect to the page for adding order items
            return redirect("add_order_items")
        else:
            messages.error(request, _("Invalid form submission. Please correct the errors."))
    else:
        po_form = PurchaseOrderForm(user_is_superuser=user_is_superuser, user_branch=user_branch)

    view_context = {"po_form": po_form}
    context = TemplateLayout.init(request, view_context)
    return render(request, "createPurchaseOrder.html", context)



@login_required
def add_order_items(request):
    user_branch = request.user.worker_profile.branch

    # Retrieve the branch from the purchase order details stored in the session
    purchase_order_details = request.session.get("purchase_order_details", {})
    selected_branch_id = purchase_order_details.get("branch")  # Branch ID from session

    # Get the actual branch object
    selected_branch = get_object_or_404(Branch, id=selected_branch_id) if selected_branch_id else user_branch

    # Initialize session data if it doesn't exist
    if "order_items" not in request.session:
        request.session["order_items"] = []

    # Pass the selected branch to the form
    item_form = PurchaseOrderItemForm(user_branch=selected_branch)

    if request.method == "POST":
        action = request.POST.get("action", "")

        # Add item to order
        if action == "add_item":
            item_form = PurchaseOrderItemForm(data=request.POST, user_branch=selected_branch)
            if item_form.is_valid():
                stock = item_form.cleaned_data["stock"]
                quantity = item_form.cleaned_data["quantity"]
                temp_price = item_form.cleaned_data["temp_price"]
                reason = item_form.cleaned_data["reason"]

                # Ensure stock availability
                if quantity > stock.total_stock:
                    messages.error(request, f"Insufficient stock: only {stock.total_stock} available.")
                else:
                    # Add item to session
                    order_items = request.session["order_items"]
                    order_items.append({
                        "stock_id": stock.id,
                        "stock_name": str(stock.product.generic_name_dosage),
                        "temp_price": float(temp_price),
                        "reason": reason,
                        "quantity": quantity,
                        "total_price": float(temp_price * quantity),
                    })
                    request.session.modified = True
                    messages.success(request, f"Added {quantity} of {stock.product.generic_name_dosage} to the order.")
            else:
                messages.error(request, _("Invalid form input. Please correct the errors."))

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
                    messages.error(request, _("Invalid item index provided."))
            except ValueError:
                messages.error(request, _("Invalid item index provided."))

        # Submit order
        elif action == "submit_order":
            order_items = request.session["order_items"]
            if order_items:
                try:
                    created_at_str = purchase_order_details.get("created_at")
                    created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')

                    # Retrieve related objects
                    customer = get_object_or_404(Customer, id=purchase_order_details.get("customer"))
                    sales_rep = get_object_or_404(Worker, id=purchase_order_details.get("sales_rep"))
                    branch = get_object_or_404(Branch, id=selected_branch_id)

                    # Handle optional payment accounts
                    momo_account = get_object_or_404(MomoInfo, id=purchase_order_details.get("momo_account_details")) if purchase_order_details.get("momo_account_details") else None
                    check_account = get_object_or_404(Check, id=purchase_order_details.get("check_account_details")) if purchase_order_details.get("check_account_details") else None
                    bank_deposit_account = get_object_or_404(BankDeposit, id=purchase_order_details.get("bank_deposit_account_details")) if purchase_order_details.get("bank_deposit_account_details") else None

                    # Convert tax fields from session (string) to Decimal
                    tax_rate = Decimal(purchase_order_details.get("tax_rate", "0.0"))
                    precompte = Decimal(purchase_order_details.get("precompte", "0.0"))
                    tva = Decimal(purchase_order_details.get("tva", "0.0"))
                    is_special_customer = purchase_order_details.get("is_special_customer", False)

                    # Calculate total
                    grand_total = sum(item["temp_price"] * item["quantity"] for item in order_items)

                    # Create purchase order
                    purchase_order = PurchaseOrder.objects.create(
                        created_at=created_at,
                        branch=branch,
                        customer=customer,
                        sales_rep=sales_rep,
                        payment_method=purchase_order_details.get("payment_method"),
                        payment_mode=purchase_order_details.get("payment_mode"),
                        momo_account=momo_account,
                        check_account=check_account,
                        bank_deposit_account=bank_deposit_account,
                        created_by=request.user.worker_profile,
                        status="Pending",
                        grand_total=grand_total,
                        tax_rate=tax_rate,
                        precompte=precompte,
                        tva=tva,
                        is_special_customer=is_special_customer,
                    )

                    # Add items to the purchase order
                    for item in order_items:
                        stock = get_object_or_404(Stock, id=item["stock_id"])
                        PurchaseOrderItem.objects.create(
                            purchase_order=purchase_order,
                            stock=stock,
                            quantity=item["quantity"],
                            temp_price=item['temp_price'],
                            reason=item['reason'],
                        )

                    # Log submission
                    worker = request.user.worker_profile if hasattr(request.user, 'worker_profile') else None
                    PurchaseOrderAuditLog.objects.create(
                        user=worker,
                        action="create",
                        order=purchase_order.purchase_order_id,
                        branch=worker.branch.branch_name if worker else "Unknown",
                        details=f"Purchase Order Created by: {worker}",
                    )

                    # Clear session and redirect
                    request.session["order_items"] = []
                    request.session["latest_purchase_order_id"] = purchase_order.id
                    request.session.modified = True
                    messages.success(request, _("Purchase order submitted successfully."))
                    return redirect("create_payment_schedule")
                except Exception as e:
                    messages.error(request, f"Error submitting the order: {e}")
            else:
                messages.error(request, _("No items added to the order."))

    # Calculate order details
    order_items = request.session["order_items"]
    grand_total = sum(item["temp_price"] * item["quantity"] for item in order_items)

    view_context = {
        "item_form": item_form,
        "order_items": order_items,
        "grand_total": grand_total,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "addOrderItems.html", context)




@login_required
def create_payment_schedule(request):
    # Retrieve the last created purchase order from the session
    purchase_order_id = request.session.get("latest_purchase_order_id")

    if not purchase_order_id:
        messages.error(request, "No purchase order found. Please create a purchase order first.")
        return redirect("create_purchase_order")

    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)

    # Check if the customer is a special customer
    is_special_customer = purchase_order.is_special_customer

    # Convert tax fields to Decimal for precise calculations
    tax_rate = Decimal(purchase_order.tax_rate or 0) / 100 if not is_special_customer else Decimal(0)  # Exempt if special
    precompte = Decimal(purchase_order.precompte or 0) / 100
    tva = Decimal(purchase_order.tva or 0) / 100

    # Calculate tax amounts
    tax_amount = purchase_order.grand_total * tax_rate
    precompte_amount = purchase_order.grand_total * precompte
    tva_amount = purchase_order.grand_total * tva

    # Final total including applicable taxes
    total_with_taxes = purchase_order.grand_total + tax_amount + precompte_amount + tva_amount

    # Initialize payment_schedules in session if not present
    if "payment_schedules" not in request.session:
        request.session["payment_schedules"] = []
        request.session.modified = True  # Mark session as changed

    # Retrieve all submitted payments linked to this purchase order
    payment_schedules = request.session.get("payment_schedules", [])

    # Convert stored amounts to Decimal for calculations
    total_scheduled = sum(Decimal(schedule["amount"]) for schedule in payment_schedules)

    # Ensure amount_left is never negative
    amount_left = total_with_taxes - total_scheduled
    if amount_left < 0:
        amount_left = 0  # Cap it to 0 if it's negative

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "add_schedule":
            form = PaymentScheduleForm(request.POST)
            if form.is_valid():
                payment_data = {
                    "when": form.cleaned_data["when"],
                    "amount": float(form.cleaned_data["amount"]),  # Convert to float
                    "payment_date": str(form.cleaned_data["payment_date"]),
                }
                request.session["payment_schedules"].append(payment_data)
                request.session.modified = True

                # Recalculate total scheduled and amount left
                total_scheduled += Decimal(payment_data["amount"])
                amount_left = total_with_taxes - total_scheduled
                if amount_left < 0:
                    amount_left = 0  # Ensure it's never negative

                messages.success(request, f"Added payment schedule for {payment_data['payment_date']}")
            else:
                messages.error(request, "Invalid form input. Please correct the errors.")

        elif action == "remove_schedule":
            try:
                index = int(request.POST.get("schedule_index", -1))
                if 0 <= index < len(request.session["payment_schedules"]):
                    removed_schedule = request.session["payment_schedules"].pop(index)
                    request.session.modified = True

                    # Add back the removed amount to `amount_left`
                    total_scheduled -= Decimal(removed_schedule["amount"])
                    amount_left = total_with_taxes - total_scheduled
                    if amount_left < 0:
                        amount_left = 0  # Ensure it's never negative

                    messages.success(request, f"Removed payment schedule for {removed_schedule['payment_date']}")
                else:
                    messages.error(request, "Invalid schedule index provided.")
            except ValueError:
                messages.error(request, "Invalid schedule index provided.")

        elif action == "submit_schedules":
            if payment_schedules:
                if amount_left > 0:
                    messages.error(request, f"Amount left to be scheduled: {amount_left:.2f} CFA. Please schedule the remaining amount before submitting.")
                else:
                    try:
                        for schedule in payment_schedules:
                            PaymentSchedule.objects.create(
                                purchase_order=purchase_order,
                                when=schedule["when"],
                                amount=Decimal(schedule["amount"]),  # Convert back to Decimal for DB storage
                                payment_date=schedule["payment_date"],
                            )

                        # Clear session after submission
                        request.session["payment_schedules"] = []
                        request.session.modified = True

                        # Recalculate total scheduled and amount left
                        total_scheduled = sum(Decimal(schedule["amount"]) for schedule in request.session["payment_schedules"])
                        amount_left = total_with_taxes - total_scheduled
                        if amount_left < 0:
                            amount_left = 0  # Ensure it's never negative

                        messages.success(request, "Payment schedules submitted successfully.")
                        return redirect("orders")
                    except Exception as e:
                        messages.error(request, f"Error submitting payment schedules: {e}")
            else:
                messages.error(request, "No payment schedules to submit.")

    form = PaymentScheduleForm()
    view_context = {
        "form": form,
        "payment_schedules": request.session["payment_schedules"],
        "purchase_order": purchase_order,
        "amount_left": amount_left,  # Ensure updated value is passed to template
        "total_with_taxes": total_with_taxes,  # Display the final total with taxes
        "tax_details": {
            "is_special_customer": is_special_customer,
            "tax_rate": tax_rate * 100,  # Convert back to percentage for display
            "precompte": precompte * 100,
            "tva": tva * 100,
            "tax_amount": tax_amount,
            "precompte_amount": precompte_amount,
            "tva_amount": tva_amount,
        },
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "createPaymentSchedule.html", context)




@login_required
def create_return_payment_schedule(request, return_invoice_id):
    # Get the return invoice and its associated return purchase order
    return_invoice = get_object_or_404(ReturnInvoice, id=return_invoice_id)

    if not return_invoice.return_purchase_order:
        messages.error(request, "No return purchase order found for this invoice.")
        return redirect("invoices")

    return_purchase_order = return_invoice.return_purchase_order

    # Extract tax details from the ReturnPurchaseOrder
    is_special_customer = return_purchase_order.is_special_customer
    tax_rate = Decimal(return_purchase_order.tax_rate or 0) / 100 if not is_special_customer else Decimal(0)  # Exempt if special
    precompte = Decimal(return_purchase_order.precompte or 0) / 100
    tva = Decimal(return_purchase_order.tva or 0) / 100

    # Calculate tax amounts
    tax_amount = return_purchase_order.grand_total * tax_rate
    precompte_amount = return_purchase_order.grand_total * precompte
    tva_amount = return_purchase_order.grand_total * tva

    # Compute total amount to be refunded (including taxes)
    total_with_taxes = return_purchase_order.grand_total + tax_amount + precompte_amount + tva_amount

    # Initialize session storage for return payment schedules
    if "return_payment_schedules" not in request.session:
        request.session["return_payment_schedules"] = []

    return_payment_schedules = request.session["return_payment_schedules"]

    # Convert stored amounts to Decimal for calculations
    total_scheduled = sum(Decimal(schedule["amount"]) for schedule in return_payment_schedules)

    # Calculate the amount left to refund (including taxes)
    amount_left = float(total_with_taxes - total_scheduled)  # Convert to float for template

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "add_schedule":
            form = PaymentScheduleForm(request.POST)
            if form.is_valid():
                payment_data = {
                    "when": form.cleaned_data["when"],
                    "amount": float(form.cleaned_data["amount"]),  # Convert to float
                    "payment_date": str(form.cleaned_data["payment_date"]),
                }
                request.session["return_payment_schedules"].append(payment_data)
                request.session.modified = True

                # Recalculate total scheduled and amount left
                total_scheduled += Decimal(payment_data["amount"])
                amount_left = float(total_with_taxes - total_scheduled)

                messages.success(request, f"Added return payment schedule for {payment_data['payment_date']}")
            else:
                messages.error(request, "Invalid form input. Please correct the errors.")

        elif action == "remove_schedule":
            try:
                index = int(request.POST.get("schedule_index", -1))
                if 0 <= index < len(request.session["return_payment_schedules"]):
                    removed_schedule = request.session["return_payment_schedules"].pop(index)
                    request.session.modified = True

                    # Add back the removed amount
                    total_scheduled -= Decimal(removed_schedule["amount"])
                    amount_left = float(total_with_taxes - total_scheduled)

                    messages.success(request, f"Removed return payment schedule for {removed_schedule['payment_date']}")
                else:
                    messages.error(request, "Invalid schedule index provided.")
            except ValueError:
                messages.error(request, "Invalid schedule index provided.")

        elif action == "submit_schedules":
            if return_payment_schedules:
                try:
                    with transaction.atomic():
                        for schedule in return_payment_schedules:
                            ReturnPaymentSchedule.objects.create(
                                return_purchase_order=return_purchase_order,
                                when=schedule["when"],
                                amount=Decimal(schedule["amount"]),  # Convert back to Decimal
                                payment_date=schedule["payment_date"],
                            )

                        # Clear session after submission
                        request.session["return_payment_schedules"] = []
                        request.session.modified = True

                        messages.success(request, "Return payment schedules submitted successfully.")
                        return redirect("invoices")
                except Exception as e:
                    messages.error(request, f"Error submitting return payment schedules: {e}")
            else:
                messages.error(request, "No return payment schedules to submit.")

    form = PaymentScheduleForm()
    view_context = {
        "form": form,
        "return_payment_schedules": request.session["return_payment_schedules"],
        "return_invoice": return_invoice,
        "amount_left": amount_left,
        "total_with_taxes": total_with_taxes,  # Display total with tax included
        "tax_details": {
            "is_special_customer": is_special_customer,
            "tax_rate": tax_rate , # Convert back to percentage for display
            "precompte": precompte,
            "tva": tva,
            "tax_amount": tax_amount,
            "precompte_amount": precompte_amount,
            "tva_amount": tva_amount,
        },
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "createPaymentSchedule.html", context)




from decimal import Decimal
from django.db import transaction

def approve_order(request, order_id):
    # Check if the user is a superadmin
    is_superadmin = request.user.is_superuser  # Assuming Django's built-in is_superuser flag

    # Fetch the order (Remove branch restriction if user is superadmin)
    if is_superadmin:
        order = get_object_or_404(PurchaseOrder, id=order_id)
    else:
        order = get_object_or_404(PurchaseOrder, id=order_id)

    notes = request.POST.get('notes', '').strip()
    if not notes:
        messages.error(request, _("Approval notes are required."))
        return redirect(reverse('order_details', args=[order_id]))

    # Check if the order is already approved or rejected
    if order.status != 'Pending':
        messages.error(request, _("This order has already been processed."))
        return redirect(reverse('order_details', args=[order_id]))

    try:
        with transaction.atomic():
            # Deduct stock and move items to TemporaryStock
            for item in order.items.all():
                stock = item.stock
                item_quantity = item.quantity

                if stock.total_stock < item_quantity:
                    messages.error(request, f"Insufficient stock for {stock.product.product_code}.")
                    return redirect(reverse('order_details', args=[order_id]))

                stock.total_sold += item_quantity
                stock.save()

                TemporaryStock.objects.create(
                    purchase_order=order,
                    stock=stock,
                    ordered_quantity=item_quantity
                )

            # Update order status
            order.status = 'Approved'
            # Assign approved_by for both superadmins and non-superadmins if worker_profile exists
            worker = request.user.worker_profile
            order.approved_by = worker  # Assign worker_profile if it exists, otherwise None
            order.notes = f"[Approval Note]: {notes} ({timezone.now().strftime('%Y-%m-%d %H:%M:%S')})"
            order.save()

            # Log action
            PurchaseOrderAuditLog.objects.create(
                user=worker,
                action="approve",
                order=order.purchase_order_id,
                branch=worker.branch.branch_name if worker else "Superadmin Approval",
                details=f"Approval Note: {order.notes}",
            )

            # Generate invoice
            invoice = Invoice.objects.create(
                branch=order.branch,
                customer=order.customer,
                sales_rep=order.sales_rep,
                payment_method=order.payment_method,
                created_at=order.created_at,
                created_by=worker,  # Assign worker_profile if it exists, otherwise None
                purchase_order=order,
                grand_total=order.grand_total,
                amount_paid=Decimal('0.00'),
                amount_due=order.grand_total
            )

            # Log invoice creation
            InvoiceAuditLog.objects.create(
                user=worker,
                action="create",
                invoice=invoice.invoice_id,
                branch=worker.branch.branch_name if worker else "Superadmin Approval",
                details=f"Invoice generated from Purchase Order: {invoice.purchase_order.purchase_order_id}",
            )

            # Create invoice items
            for item in order.items.all():
                InvoiceOrderItem.objects.create(
                    invoice_order=invoice,
                    stock=item.stock,
                    quantity=item.quantity,
                    price=item.get_effective_price()
                )

            messages.success(request, _("Order approved and invoice generated successfully."))
            return redirect(reverse('order_details', args=[order_id]))

    except Exception as e:
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


from decimal import Decimal

@login_required
def view_purchase_order(request, purchase_order_id):
    user = request.user
    worker = user.worker_profile

    is_accountant_or_superuser = user.is_superuser or worker.role == "Accountant"

    # Try to fetch the order as a PurchaseOrder
    order = None
    try:
        if is_accountant_or_superuser:
            order = get_object_or_404(PurchaseOrder, purchase_order_id=purchase_order_id)
        else:
            order = get_object_or_404(PurchaseOrder, purchase_order_id=purchase_order_id, branch=worker.branch)
        order_type = "purchase_order"
    except Http404:
        # If not a PurchaseOrder, try fetching as a ReturnPurchaseOrder
        if is_accountant_or_superuser:
            order = get_object_or_404(ReturnPurchaseOrder, return_order_id=purchase_order_id)
        else:
            order = get_object_or_404(ReturnPurchaseOrder, return_order_id=purchase_order_id, branch=worker.branch)
        order_type = "return_purchase_order"

    # Fetch order items based on the order type
    if order_type == "purchase_order":
        order_items = PurchaseOrderItem.objects.filter(purchase_order=order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F('temp_price')),
                default=F('stock__product__unit_price'),
                output_field=FloatField()
            ),
            total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
        )
    else:
        order_items = ReturnPurchaseOrderItem.objects.filter(return_purchase_order=order).annotate(
            effective_price=Case(
                When(temp_price__isnull=False, then=F('temp_price')),
                default=F('stock__product__unit_price'),
                output_field=FloatField()
            ),
            total_price=ExpressionWrapper(F('quantity') * F('effective_price'), output_field=FloatField())
        )

    total_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    worker_privileges = worker.privileges.values_list('name', flat=True)
    payment_schedules = PaymentSchedule.objects.filter(purchase_order=order) if order_type == "purchase_order" else []

    grand_total = order.grand_total

    # Convert tax rates to Decimal to avoid TypeError
    tax_rate = Decimal(order.tax_rate or 0)
    precompte = Decimal(order.precompte or 0)
    tva = Decimal(order.tva or 0)

    # Calculate tax amounts
    tax_amount = (grand_total * tax_rate) / Decimal(100)
    tva_amount = (grand_total * tva) / Decimal(100)
    precompte_amount = (grand_total * precompte) / Decimal(100)

    # Calculate the new total
    if order.is_special_customer:
        new_total = grand_total + tva_amount + precompte_amount
    else:
        new_total = grand_total + tva_amount + tax_amount + precompte_amount

    view_context = {
        "order": order,
        "order_items": order_items,
        "total_quantity": total_quantity,
        "worker_privileges": worker_privileges,
        "payment_schedules": payment_schedules,
        "grand_total": grand_total,
        "tva": tva,
        "tva_amount": tva_amount,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "precompte": precompte,
        "precompte_amount": precompte_amount,
        "new_total": new_total,
        "is_special_customer": order.is_special_customer,
        "order_type": order_type,  # Pass the order type to the template
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'purchase_order.html', context)





@login_required
def reject_order(request, order_id):
    # Fetch the order
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    # Check if the order is already approved or rejected
    if order.status != 'Pending':
        messages.error(request, _("This order has already been processed."))
        return redirect(reverse('order_details', args=[order_id]))

    if request.method == 'POST':
        # Get the rejection reason
        notes = request.POST.get('notes', '').strip()
        if not notes:
            messages.error(request, _("Rejection notes are required."))
            return redirect(reverse('order_details', args=[order_id]))

        # Update order status and notes
        order.status = 'Rejected'
        order.notes = notes
        order.save()

        # Log the submission action
        try:
            worker = request.user.worker_profile
        except AttributeError:
            worker = None
        PurchaseOrderAuditLog.objects.create(
            user=worker,  # Assuming `request.user` is linked to a worker
            action="reject",
            order=order.purchase_order_id,
            branch=worker.branch.branch_name,
            details=f"Rejection Note: {order.notes}",
        )

        messages.success(request, _("Order rejected successfully."))
        return redirect(reverse('order_details', args=[order_id]))

    # If not POST, return error response
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def cancel_order(request, order_id):
    # Fetch the order
    order = get_object_or_404(PurchaseOrder, id=order_id, branch=request.user.worker_profile.branch)

    # Ensure only Pending or Approved orders can be canceled
    if order.status not in ['Pending', 'Approved']:
        messages.error(request, _("Only pending or approved orders can be canceled."))
        return redirect(reverse('order_details', args=[order_id]))

    # Check if an invoice is linked to the purchase order
    invoice = Invoice.objects.filter(purchase_order=order).first()

    if invoice:
        # Ensure the invoice is unpaid before cancellation
        if invoice.status != 'Unpaid':
            messages.error(request, _("This order cannot be canceled because a payment has already been made."))
            return redirect(reverse('order_details', args=[order_id]))

    # Perform cancellation
    if request.method == 'POST':
        try:
            # Restore stock if applicable
            order_items = PurchaseOrderItem.objects.filter(purchase_order=order)
            for item in order_items:
                stock = item.stock

                # Restore the stock quantity
                stock.total_stock += item.quantity
                stock.save()

                # Remove the item from the TemporaryStock table
                TemporaryStock.objects.filter(
                    purchase_order=order,
                    stock=stock
                ).delete()

            # Update the order status to "Canceled"
            order.status = 'Canceled'
            order.save()

            # If an unpaid invoice exists, cancel it as well
            if invoice:
                invoice.status = 'Canceled'
                invoice.save()

            # Log the cancellation action
            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None
            PurchaseOrderAuditLog.objects.create(
                user=worker,
                action="cancel",
                order=order.purchase_order_id,
                branch=worker.branch.branch_name,
                details=f"Purchase Order Cancelled By: {worker}",
            )

            messages.success(request, _("Order and linked invoice (if unpaid) canceled successfully."))
            return redirect(reverse('order_details', args=[order_id]))

        except Exception as e:
            messages.error(request, f"An error occurred while canceling the order: {e}")
            return redirect(reverse('order_details', args=[order_id]))

    # If not POST, return an error response
    return JsonResponse({'error': 'Invalid request method'}, status=400)




@login_required
def edit_prices(request, order_id):
    user = request.user
    worker = getattr(user, "worker_profile", None)

    # Check if the user has Accountant privileges or is a superuser
    is_accountant_or_superuser = user.is_superuser or (worker and worker.role == "Accountant")

    if not is_accountant_or_superuser:
        messages.error(request, _("You do not have permission to edit prices for this order."))
        return redirect("order_details", order_id=order_id)

    if request.method == "POST":
        order = None
        order_items = None
        order_type = None

        # Check if it's a PurchaseOrder or ReturnPurchaseOrder
        if user.is_superuser:
            order = PurchaseOrder.objects.filter(id=order_id).first()
            if order:
                order_items = PurchaseOrderItem.objects.filter(purchase_order=order)
                order_type = "purchase_order"
            else:
                order = ReturnPurchaseOrder.objects.filter(id=order_id).first()
                if order:
                    order_items = ReturnPurchaseOrderItem.objects.filter(return_purchase_order=order)
                    order_type = "return_purchase_order"
        else:
            order = PurchaseOrder.objects.filter(id=order_id, branch=worker.branch).first()
            if order:
                order_items = PurchaseOrderItem.objects.filter(purchase_order=order)
                order_type = "purchase_order"
            else:
                order = ReturnPurchaseOrder.objects.filter(id=order_id, branch=worker.branch).first()
                if order:
                    order_items = ReturnPurchaseOrderItem.objects.filter(return_purchase_order=order)
                    order_type = "return_purchase_order"

        if not order:
            messages.error(request, _("No valid order found."))
            return redirect("order_details", order_id=order_id)

        try:
            with transaction.atomic():
                # Capture the reason for price change
                edit_price_note = request.POST.get("edit_price_note", "").strip()
                if not edit_price_note:
                    messages.error(request, _("Please provide a reason for the price change."))
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
                        When(temp_price__isnull=False, then=F("temp_price")),
                        default=F("stock__product__unit_price"),
                        output_field=FloatField(),
                    ),
                    total_price=F("quantity") * F("effective_price"),
                ).aggregate(total=Sum("total_price"))["total"]

                # Update the grand total in the order
                order.grand_total = grand_total

                # Overwrite the note with the new reason
                order.notes = f"[Price Change]: {edit_price_note} ({timezone.now().strftime('%Y-%m-%d %H:%M:%S')})"
                order.save()

                # ✅ Update payment schedule if "Upon Delivery"
                payment_schedule = PaymentSchedule.objects.filter(
                    purchase_order=order, when="Upon Delivery"
                ).first()

                if payment_schedule:
                    payment_schedule.amount = str(grand_total)  # Store as a string (matches model)
                    payment_schedule.save()

                messages.success(request, _("Prices and grand total updated successfully for this order."))

        except Exception as e:
            messages.error(request, f"An error occurred while updating prices: {e}")

        return redirect("order_details", order_id=order_id)

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
    worker = get_object_or_404(Worker, id=worker_id, role="Sales Rep")

    # Fetch all credit invoices linked to this worker
    credit_invoices = OldInvoiceOrder.objects.filter(
        sales_rep=worker,
        payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid")
    ).order_by("-created_at")

    # Fetch current credit orders from Invoice
    current_credit_orders = Invoice.objects.filter(
        sales_rep=worker, payment_method="Credit"
    ).annotate(
        calculated_amount_due=F("grand_total") - F("amount_paid"),
    ).order_by("-created_at")

    current_invoice = current_credit_orders.first()

    # Calculate totals
    total_due_old = credit_invoices.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    total_due_current = current_credit_orders.aggregate(total_due=Sum("calculated_amount_due"))["total_due"] or 0
    total_due_general = total_due_old + total_due_current

    total_amount_paid_old = credit_invoices.aggregate(total_paid=Sum("amount_paid"))["total_paid"] or 0
    total_amount_paid_current = current_credit_orders.aggregate(total_paid=Sum("amount_paid"))["total_paid"] or 0
    total_amount_paid = total_amount_paid_old + total_amount_paid_current

    total_grand_total_old = credit_invoices.aggregate(total=Sum("grand_total"))["total"] or 0
    total_grand_total_current = current_credit_orders.aggregate(total=Sum("grand_total"))["total"] or 0
    total_grand_total = total_grand_total_old + total_grand_total_current

    total_sold = total_amount_paid + total_due_general

    # Calculate percentages with proper handling for zero total
    if total_grand_total > 0:
        total_percentage_paid = (total_amount_paid / total_grand_total) * 100
        total_percentage_left = 100 - total_percentage_paid
    else:
        total_percentage_paid = 0
        total_percentage_left = 0


    # Context data
    view_context = {
        "worker": worker,
        "credit_invoices": credit_invoices,
        "current_credit_orders": current_credit_orders,
        "current_invoice": current_invoice,
        "total_sold": total_sold,
        "total_due_old": total_due_old,
        "total_due_current": total_due_current,
        "total_due_general": total_due_general,
        "total_amount_paid": total_amount_paid,
        "total_percentage_paid": total_percentage_paid,
        "total_percentage_left": total_percentage_left,
        "current_date": now(),
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, "salesRepCreditReport.html", context)



@login_required
def add_invoice_payment(request, invoice_id):
    """
    Handles both normal invoice payments and return invoice payments dynamically.
    """
    # Check if it's a normal invoice or a return invoice
    invoice = Invoice.objects.filter(id=invoice_id).first()
    return_invoice = ReturnInvoice.objects.filter(id=invoice_id).first()

    if not invoice and not return_invoice:
        messages.error(request, "Invalid invoice reference.")
        return redirect('invoice_list')

    # Determine which form to use
    is_return_invoice = bool(return_invoice)
    invoice_instance = return_invoice if is_return_invoice else invoice
    form_class = ReturnInvoicePaymentForm if is_return_invoice else InvoicePaymentForm

    # Use the correct total (including taxes)
    total_with_taxes = invoice_instance.total_with_taxes

    if request.method == 'POST':
        form = form_class(request.POST, invoice=invoice_instance)

        if form.is_valid():
            payment_amount = form.cleaned_data['amount_paid']
            payment_mode = form.cleaned_data['payment_mode']
            notes = form.cleaned_data.get('notes', '')

            momo_account = form.cleaned_data.get('momo_account') if payment_mode == "Mobile Money" else None
            check_account = form.cleaned_data.get('check_account') if payment_mode == "Check" else None
            bank_deposit_account = form.cleaned_data.get('bank_deposit_account') if payment_mode == "Bank Deposit" else None

            # Validation: Ensure payment doesn't exceed due amount
            if payment_amount > total_with_taxes:
                form.add_error('amount_paid', _("Payment amount cannot exceed the invoice's total with taxes."))
            elif payment_amount > invoice_instance.amount_due:
                form.add_error('amount_paid', _("Payment amount cannot exceed the remaining amount due."))
            else:
                with transaction.atomic():
                    # Update invoice payment status
                    invoice_instance.amount_paid += payment_amount
                    invoice_instance.amount_due = max(total_with_taxes - invoice_instance.amount_paid, 0)

                    if invoice_instance.amount_paid == total_with_taxes:
                        invoice_instance.status = 'Payment Completed'
                    elif invoice_instance.amount_paid > 0:
                        invoice_instance.status = 'Payment Ongoing'
                    else:
                        invoice_instance.status = 'Unpaid'

                    invoice_instance.save()

                    # ✅ Save the payment
                    payment = form.save(commit=False)
                    payment.return_invoice = return_invoice if is_return_invoice else None
                    payment.invoice = invoice if not is_return_invoice else None
                    payment.invoice_total = total_with_taxes  # Use tax-inclusive total
                    payment.momo_account = momo_account
                    payment.check_account = check_account
                    payment.bank_deposit_account = bank_deposit_account
                    payment.save()

                    # ✅ Generate the correct type of receipt
                    if is_return_invoice:
                        receipt = ReturnReceipt.objects.create(
                            return_invoice=return_invoice,
                            return_invoice_payment=payment,
                            amount_paid=payment_amount,
                            payment_method=payment_mode,
                            notes=notes,
                        )
                    else:
                        receipt = Receipt.objects.create(
                            invoice=invoice,
                            invoice_payment=payment,
                            amount_paid=payment_amount,
                            payment_method=payment_mode,
                            notes=notes,
                        )

                messages.success(request, f"Payment added successfully! Receipt ID: {receipt.receipt_id}")

                # ✅ Redirect to the correct receipt type
                return redirect('receipt_doc', receipt_id=receipt.receipt_id)

    else:
        form = form_class(invoice=invoice_instance)

    view_context = {
        'invoice': invoice_instance,
        'form': form,
        'is_return_invoice': is_return_invoice,
        'total_with_taxes': total_with_taxes,  # Pass tax-inclusive total to template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'makePayment.html', context)






@login_required
def add_bank_details_view(request, pk=None):
    bank_details = Bank.objects.all()
    if pk:
        bank_details = get_object_or_404(Bank, pk=pk)
        form = BankForm(request.POST or None, instance=bank_details)
        action = "update"  # Specify the action for logs
    else:
        bank_details = None
        form = BankForm(request.POST or None)
        action = "create"  # Specify the action for logs

    if request.method == "POST":
        if form.is_valid():

            # Save the form data first to create/update the Bank instance
            bank_details = form.save(commit=False)  # Don't save to DB yet

            # Log the action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            if action == "create" and worker:
                bank_details.created_by = worker

            bank_details.save()  # Save the form data

            # Set success message and redirect
            messages.success(
                request, _("Bank Details {action}d successfully!".format(action=action))
            )
            return redirect('add-bank')  # Redirect to generic name listing page
    all_bank_details = Bank.objects.all()

    view_context = {
        "form": form,
        "bank_details": all_bank_details,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_bankDetails.html', context)


@login_required
def edit_bank_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    bank_details = get_object_or_404(Bank, pk=pk)
    all_bank_details = Bank.objects.all()

    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = BankForm(request.POST, instance=bank_details)
        if form.is_valid():
            form.save()

            # # Log the update action
            # try:
            #     worker = request.user.worker_profile  # Fetch worker profile
            # except AttributeError:
            #     worker = None  # Handle case where no worker profile is linked

            # log_details = f"Generic Name '{generic_name.generic_name}' updated by {'admin' if worker is None else worker}."
            # GenericNameAuditLog.objects.create(
            #     user=worker,
            #     generic_name=generic_name.generic_name,
            #     action="update",
            #     details=log_details
            # )

            messages.success(request, _("Bank details updated successfully!"))
            return redirect('add-bank')  # Redirect to the appropriate page
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        # Populate the form with existing data for GET requests
        form = BankForm(instance=bank_details)

    view_context = {
        "form": form,
        "bank_details": all_bank_details,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_bankDetails.html', context)



@login_required
def delete_bank_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    bank_details = get_object_or_404(Bank, pk=pk)

    if request.method == "POST":
        # # Log the delete action before deleting the instance
        # try:
        #     worker = request.user.worker_profile  # Fetch worker profile
        # except AttributeError:
        #     worker = None  # Handle case where no worker profile is linked

        # log_details = f"Generic Name '{generic_name.generic_name}' deleted by {'admin' if worker is None else worker}."
        # GenericNameAuditLog.objects.create(
        #     user=worker,
        #     generic_name=generic_name.generic_name,
        #     action="delete",
        #     details=log_details
        # )

        # Delete the instance
        bank_details.delete()
        messages.success(request, _("Bank Details deleted successfully!"))
        return redirect('add-bank')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_bank_details = Bank.objects.all()

    view_context = {
        "bank_details": all_bank_details,  # To display the list of generic names
        "item_to_delete": bank_details,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_bankDetails.html', context)



@login_required
def add_momo_details_view(request, pk=None):
    momo_details = MomoInfo.objects.all()
    if pk:
        momo_details = get_object_or_404(MomoInfo, pk=pk)
        form = MomoInfoForm(request.POST or None, instance=momo_details)
        action = "update"  # Specify the action for logs
    else:
        momo_details = None
        form = MomoInfoForm(request.POST or None)
        action = "create"  # Specify the action for logs

    if request.method == "POST":
        if form.is_valid():

            # Save the form data first to create/update the Bank instance
            momo_details = form.save(commit=False)  # Don't save to DB yet

            # Log the action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            if action == "create" and worker:
                momo_details.created_by = worker

            momo_details.save()  # Save the form data

            # Set success message and redirect
            messages.success(
                request, _("Momo Details {action}d successfully!".format(action=action))
            )
            return redirect('add-momo')  # Redirect to generic name listing page
    all_momo_details = MomoInfo.objects.all()

    view_context = {
        "form": form,
        "momo_details": all_momo_details,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_momo.html', context)


@login_required
def edit_momo_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    momo_details = get_object_or_404(MomoInfo, pk=pk)
    all_momo_details = MomoInfo.objects.all()

    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = MomoInfoForm(request.POST, instance=momo_details)
        if form.is_valid():
            form.save()

            # # Log the update action
            # try:
            #     worker = request.user.worker_profile  # Fetch worker profile
            # except AttributeError:
            #     worker = None  # Handle case where no worker profile is linked

            # log_details = f"Generic Name '{generic_name.generic_name}' updated by {'admin' if worker is None else worker}."
            # GenericNameAuditLog.objects.create(
            #     user=worker,
            #     generic_name=generic_name.generic_name,
            #     action="update",
            #     details=log_details
            # )

            messages.success(request, _("Momo details updated successfully!"))
            return redirect('add-momo')  # Redirect to the appropriate page
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        # Populate the form with existing data for GET requests
        form = MomoInfoForm(instance=momo_details)

    view_context = {
        "form": form,
        "momo_details": all_momo_details,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_momo.html', context)



@login_required
def delete_momo_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    momo_details = get_object_or_404(MomoInfo, pk=pk)

    if request.method == "POST":
        # # Log the delete action before deleting the instance
        # try:
        #     worker = request.user.worker_profile  # Fetch worker profile
        # except AttributeError:
        #     worker = None  # Handle case where no worker profile is linked

        # log_details = f"Generic Name '{generic_name.generic_name}' deleted by {'admin' if worker is None else worker}."
        # GenericNameAuditLog.objects.create(
        #     user=worker,
        #     generic_name=generic_name.generic_name,
        #     action="delete",
        #     details=log_details
        # )

        # Delete the instance
        momo_details.delete()
        messages.success(request, _("Momo Details deleted successfully!"))
        return redirect('add-momo')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_momo_details = MomoInfo.objects.all()

    view_context = {
        "momo_details": all_momo_details,  # To display the list of generic names
        "item_to_delete": momo_details,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_momo.html', context)


@login_required
def add_check_details_view(request, pk=None):
    check_details = Check.objects.all()
    if pk:
        check_details = get_object_or_404(Check, pk=pk)
        form = CheckForm(request.POST or None, instance=check_details)
        action = "update"  # Specify the action for logs
    else:
        check_details = None
        form = CheckForm(request.POST or None)
        action = "create"  # Specify the action for logs

    if request.method == "POST":
        if form.is_valid():

            # Save the form data first to create/update the Bank instance
            check_details = form.save(commit=False)  # Don't save to DB yet

            # Log the action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            if action == "create" and worker:
                check_details.created_by = worker

            check_details.save()  # Save the form data

            # Set success message and redirect
            messages.success(
                request, _("Check Details {action}d successfully!".format(action=action))
            )
            return redirect('add-check')  # Redirect to generic name listing page
    all_check_details = Check.objects.all()

    view_context = {
        "form": form,
        "check_details": all_check_details,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_check.html', context)


@login_required
def edit_check_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    check_details = get_object_or_404(Check, pk=pk)
    all_check_details = Check.objects.all()

    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = CheckForm(request.POST, instance=check_details)
        if form.is_valid():
            form.save()

            # # Log the update action
            # try:
            #     worker = request.user.worker_profile  # Fetch worker profile
            # except AttributeError:
            #     worker = None  # Handle case where no worker profile is linked

            # log_details = f"Generic Name '{generic_name.generic_name}' updated by {'admin' if worker is None else worker}."
            # GenericNameAuditLog.objects.create(
            #     user=worker,
            #     generic_name=generic_name.generic_name,
            #     action="update",
            #     details=log_details
            # )

            messages.success(request, _("Check details updated successfully!"))
            return redirect('add-check')  # Redirect to the appropriate page
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        # Populate the form with existing data for GET requests
        form = CheckForm(instance=check_details)

    view_context = {
        "form": form,
        "check_details": all_check_details,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_check.html', context)



@login_required
def delete_check_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    check_details = get_object_or_404(Check, pk=pk)

    if request.method == "POST":
        # # Log the delete action before deleting the instance
        # try:
        #     worker = request.user.worker_profile  # Fetch worker profile
        # except AttributeError:
        #     worker = None  # Handle case where no worker profile is linked

        # log_details = f"Generic Name '{generic_name.generic_name}' deleted by {'admin' if worker is None else worker}."
        # GenericNameAuditLog.objects.create(
        #     user=worker,
        #     generic_name=generic_name.generic_name,
        #     action="delete",
        #     details=log_details
        # )

        # Delete the instance
        check_details.delete()
        messages.success(request, _("Check Details deleted successfully!"))
        return redirect('add-check')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_check_details = Check.objects.all()

    view_context = {
        "check_details": all_check_details,  # To display the list of generic names
        "item_to_delete": check_details,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_check.html', context)



@login_required
def add_deposit_details_view(request, pk=None):
    deposit_details = BankDeposit.objects.all()
    if pk:
        deposit_details = get_object_or_404(BankDeposit, pk=pk)
        form = BankDepositForm(request.POST or None, instance=deposit_details)
        action = "update"  # Specify the action for logs
    else:
        deposit_details = None
        form = BankDepositForm(request.POST or None)
        action = "create"  # Specify the action for logs

    if request.method == "POST":
        if form.is_valid():

            # Save the form data first to create/update the Bank instance
            deposit_details = form.save(commit=False)  # Don't save to DB yet

            # Log the action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            if action == "create" and worker:
                deposit_details.created_by = worker

            deposit_details.save()  # Save the form data

            # Set success message and redirect
            messages.success(
                request, _("Bank Deposit Details {action}d successfully!".format(action=action))
            )
            return redirect('add-deposit')  # Redirect to generic name listing page
    all_deposit_details = BankDeposit.objects.all()

    view_context = {
        "form": form,
        "deposit_details": all_deposit_details,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_deposit.html', context)


@login_required
def edit_deposit_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    deposit_details = get_object_or_404(BankDeposit, pk=pk)
    all_deposit_details = BankDeposit.objects.all()

    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = BankDepositForm(request.POST, instance=deposit_details)
        if form.is_valid():
            form.save()

            # # Log the update action
            # try:
            #     worker = request.user.worker_profile  # Fetch worker profile
            # except AttributeError:
            #     worker = None  # Handle case where no worker profile is linked

            # log_details = f"Generic Name '{generic_name.generic_name}' updated by {'admin' if worker is None else worker}."
            # GenericNameAuditLog.objects.create(
            #     user=worker,
            #     generic_name=generic_name.generic_name,
            #     action="update",
            #     details=log_details
            # )

            messages.success(request, _("Bank Deposit details updated successfully!"))
            return redirect('add-deposit')  # Redirect to the appropriate page
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        # Populate the form with existing data for GET requests
        form = BankDepositForm(instance=deposit_details)

    view_context = {
        "form": form,
        "deposit_details": all_deposit_details,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_deposit.html', context)



@login_required
def delete_deposit_details_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    deposit_details = get_object_or_404(BankDeposit, pk=pk)

    if request.method == "POST":
        # # Log the delete action before deleting the instance
        # try:
        #     worker = request.user.worker_profile  # Fetch worker profile
        # except AttributeError:
        #     worker = None  # Handle case where no worker profile is linked

        # log_details = f"Generic Name '{generic_name.generic_name}' deleted by {'admin' if worker is None else worker}."
        # GenericNameAuditLog.objects.create(
        #     user=worker,
        #     generic_name=generic_name.generic_name,
        #     action="delete",
        #     details=log_details
        # )

        # Delete the instance
        deposit_details.delete()
        messages.success(request, _("Bank Deposit Details deleted successfully!"))
        return redirect('add-deposit')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_deposit_details = BankDeposit.objects.all()

    view_context = {
        "deposit_details": all_deposit_details,  # To display the list of generic names
        "item_to_delete": deposit_details,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_deposit.html', context)




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
