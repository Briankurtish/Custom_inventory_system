from datetime import datetime
from django.utils import timezone
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField, Q
from .forms import ActualQuantityForm, ActualTransferQuantityForm, StockRequestForm, StockRequestDocumentForm, StockTransferDocumentForm, StockTransferForm
from apps.products.models import Batch, Product
from apps.branches.models import Branch
from .models import StockRequest, StockRequestAuditLog, StockRequestProduct, InTransit, StockRequestDocument, StockTransfer, StockTransferAuditLog, StockTransferDocument, StockTransferItem
from apps.stock.models import Stock
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
from django.core.files import File
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""
@login_required
def stock_request_view(request):
    form = StockRequestForm(user=request.user)
    temp_stock_request_list = request.session.get("TEMP_STOCK_REQUEST_LIST", [])

    if request.method == "POST":
        if "add_to_request_list" in request.POST:
            form = StockRequestForm(request.POST, user=request.user)
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                branch = form.cleaned_data["branch"]
                requested_at = form.cleaned_data["requested_at"]
                batch = product.batch  # Use the batch from the selected product
                batch_number = batch.batch_number if batch else None

                if not batch:
                    messages.error(request, _(f"No batch specified for {product.generic_name_dosage}."))
                    return redirect("create-request")

                # Fetch the stock only from Central Warehouse
                central_warehouse = Branch.objects.filter(branch_name="Central Warehouse").first()
                if not central_warehouse:
                    messages.error(request, _("Central Warehouse not found. Please check the configuration."))
                    return redirect("create-request")

                # Check stock using the product and batch
                central_stock = Stock.objects.filter(branch=central_warehouse, product=product, batch=batch).first()
                if not central_stock:
                    print(f"Stock not found for Product ID: {product.id}, Batch: {batch_number}, Branch: {central_warehouse.branch_name}")
                    print(f"All stock for Product ID {product.id}: {Stock.objects.filter(product=product).values('branch__branch_name', 'batch__batch_number', 'total_stock')}")
                if not central_stock or central_stock.total_stock < quantity:
                    messages.warning(
                        request,
                        _(f"Insufficient stock in Central Warehouse for {product.generic_name_dosage} (Batch: {batch_number}). "
                          f"Requested: {quantity}, Available: {central_stock.total_stock if central_stock else 0}")
                    )
                    return redirect("create-request")

                # Check if the same product with the same batch already exists in the list using product_id
                existing_item = next(
                    (item for item in temp_stock_request_list
                     if item["product_id"] == product.id
                     and item["branch_id"] == branch.id
                     and item["batch_number"] == batch_number),
                    None
                )

                if existing_item:
                    existing_item["quantity"] += quantity
                else:
                    temp_stock_request_list.append({
                        "product_id": product.id,
                        "product_code": product.product_code,
                        "batch_number": batch_number,
                        "product_name": str(product.generic_name_dosage),
                        "brand_name": str(product.brand_name.brand_name) if product.brand_name else "No Brand",
                        "quantity": quantity,
                        "branch_id": branch.id,
                        "branch_name": branch.branch_name,
                        "requested_at": str(requested_at),
                    })
                    print(f"Added item to temp_stock_request_list: {temp_stock_request_list[-1]}")  # Debug log

                request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
                messages.success(request, _("Item added to temporary stock request list."))
            else:
                messages.error(request, _("Invalid form submission."))

        elif "remove_item" in request.POST:
            product_id = request.POST.get("product_id")
            branch_id = request.POST.get("branch")
            batch_number = request.POST.get("batch_number")

            # Validate inputs
            if not product_id or not branch_id or not batch_number:
                print(f"Missing fields in remove_item: product_id={product_id}, branch_id={branch_id}, batch_number={batch_number}")
                messages.error(request, _("Missing required fields to remove item."))
                return redirect("create-request")

            try:
                product_id = int(product_id)
                branch_id = int(branch_id)
            except (ValueError, TypeError) as e:
                print(f"Error converting fields: product_id={product_id}, branch_id={branch_id}, error={str(e)}")
                messages.error(request, _("Invalid data provided for removing item."))
                return redirect("create-request")

            temp_stock_request_list = [
                item for item in temp_stock_request_list
                if not (
                    item["product_id"] == product_id
                    and item["branch_id"] == branch_id
                    and item["batch_number"] == batch_number
                )
            ]
            request.session["TEMP_STOCK_REQUEST_LIST"] = temp_stock_request_list
            messages.success(request, _("Item removed from the temporary stock request list."))

        elif "submit_request" in request.POST:
            if temp_stock_request_list:
                branch_ids = {item["branch_id"] for item in temp_stock_request_list}
                if len(branch_ids) > 1:
                    messages.error(request, _("All requested stock items must belong to the same branch."))
                    return redirect("create-request")

                branch = Branch.objects.get(id=temp_stock_request_list[0]["branch_id"])
                requested_at = temp_stock_request_list[0]["requested_at"]

                try:
                    worker = request.user.worker_profile
                except AttributeError:
                    messages.error(request, _("You do not have a worker profile. Please contact the administrator."))
                    return redirect("create-request")

                stock_request = StockRequest.objects.create(
                    branch=branch,
                    requested_by=worker,
                    requested_at=requested_at,
                    request_type=StockRequest.NORMAL
                )

                for item in temp_stock_request_list:
                    product = Product.objects.filter(id=item["product_id"]).first()
                    batch_number = item["batch_number"]
                    quantity_requested = item["quantity"]

                    # Retrieve the batch object based on the batch_number
                    batch = Batch.objects.filter(batch_number=batch_number).first()
                    if not batch:
                        messages.error(request, _(f"Batch {batch_number} not found for product {product.generic_name_dosage}."))
                        stock_request.delete()
                        return redirect("create-request")

                    StockRequestProduct.objects.create(
                        stock_request=stock_request,
                        product=product,
                        quantity=quantity_requested,
                        batch=batch
                    )

                StockRequestAuditLog.objects.create(
                    user=worker,
                    action="Stock Request Created",
                    request=stock_request.request_number,
                    branch=branch.branch_name,
                    details=f"New Stock Request for: {branch.branch_name}",
                )

                del request.session["TEMP_STOCK_REQUEST_LIST"]
                messages.success(request, _("Stock request submitted successfully."))
                return redirect("requests")

    view_context = {
        "form": form,
        "temp_stock_request": temp_stock_request_list,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'createRequests.html', context)



@login_required
def stock_transfer_view(request):
    form = StockTransferForm(user=request.user)
    temp_transfer_list = request.session.get("TEMP_TRANSFER_LIST", [])

    if request.method == "POST":
        if "add_to_transfer_list" in request.POST:
            form = StockTransferForm(request.POST, user=request.user)
            if form.is_valid():
                product = form.cleaned_data["product"]
                quantity = form.cleaned_data["quantity"]
                source_branch = form.cleaned_data["source_branch"]
                destination_branch = form.cleaned_data["destination_branch"]
                date_transferred = form.cleaned_data["date_transferred"]
                batch = product.batch

                if not batch:
                    messages.error(request, _(f"No batch specified for {product.generic_name_dosage}."))
                    return redirect("create-transfer")

                batch_number = batch.batch_number

                # Debug: Log the query details using product_id
                print(f"Checking stock - Product ID: {product.id}, "
                      f"Batch: {batch_number} (ID: {batch.id}), "
                      f"Branch: {source_branch.branch_name} (ID: {source_branch.id})")
                source_stock = Stock.objects.filter(
                    branch=source_branch,
                    product=product,
                    batch=batch
                ).first()
                print(f"Source stock result: {source_stock}")

                # Additional debug: Check all stock for this product and batch
                if not source_stock:
                    print(f"All stock for Product ID {product.id}: {Stock.objects.filter(product=product).values('branch__branch_name', 'batch__batch_number', 'total_stock')}")
                    print(f"All stock for Batch ID {batch.id}: {Stock.objects.filter(batch=batch).values('branch__branch_name', 'product__product_code', 'total_stock')}")
                    print(f"All stock in Branch ID {source_branch.id}: {Stock.objects.filter(branch=source_branch).values('product__product_code', 'batch__batch_number', 'total_stock')}")

                if not source_stock or source_stock.total_stock < quantity:
                    messages.warning(
                        request,
                        _(f"Insufficient stock in {source_branch.branch_name} for {product.generic_name_dosage} (Batch: {batch_number}). "
                          f"Requested: {quantity}, Available: {source_stock.total_stock if source_stock else 0}")
                    )
                    return redirect("create-transfer")

                # Check if the same product with the same batch already exists in the list using product_id
                existing_item = next(
                    (item for item in temp_transfer_list
                     if item["product_id"] == product.id  # Use product_id instead of product_code
                     and item["batch_number"] == batch_number
                     and item["source_branch_id"] == source_branch.id
                     and item["destination_branch_id"] == destination_branch.id),
                    None
                )

                if existing_item:
                    existing_item["quantity"] += quantity
                else:
                    temp_transfer_list.append({
                        "product_id": product.id,  # Use product_id instead of product_code
                        "product_code": product.product_code,  # Keep product_code for display
                        "batch_number": batch_number,
                        "product_name": str(product.generic_name_dosage),
                        "brand_name": str(product.brand_name.brand_name) if product.brand_name else "No Brand",
                        "quantity": quantity,
                        "source_branch_id": source_branch.id,
                        "source_branch_name": source_branch.branch_name,
                        "destination_branch_id": destination_branch.id,
                        "destination_branch_name": destination_branch.branch_name,
                        "date_transferred": str(date_transferred),
                    })
                    print(f"Added item to temp_transfer_list: {temp_transfer_list[-1]}")  # Debug log

                request.session["TEMP_TRANSFER_LIST"] = temp_transfer_list
                messages.success(request, _("Item added to temporary transfer list."))
            else:
                messages.error(request, _("Invalid form submission."))

        elif "remove_item" in request.POST:
            product_id = request.POST.get("product_id")  # Use product_id instead of product_code
            batch_number = request.POST.get("batch_number")
            source_branch_id = request.POST.get("source_branch")
            destination_branch_id = request.POST.get("destination_branch")

            # Validate inputs
            if not product_id or not batch_number or not source_branch_id or not destination_branch_id:
                print(f"Missing fields in remove_item: product_id={product_id}, batch_number={batch_number}, "
                      f"source_branch_id={source_branch_id}, destination_branch_id={destination_branch_id}")
                messages.error(request, _("Missing required fields to remove item."))
                return redirect("create-transfer")

            try:
                product_id = int(product_id)
                source_branch_id = int(source_branch_id)
                destination_branch_id = int(destination_branch_id)
            except (ValueError, TypeError) as e:
                print(f"Error converting fields: product_id={product_id}, source_branch_id={source_branch_id}, "
                      f"destination_branch_id={destination_branch_id}, error={str(e)}")
                messages.error(request, _("Invalid data provided for removing item."))
                return redirect("create-transfer")

            item_to_remove = next(
                (item for item in temp_transfer_list
                 if item["product_id"] == product_id  # Use product_id
                 and item["batch_number"] == batch_number
                 and item["source_branch_id"] == source_branch_id
                 and item["destination_branch_id"] == destination_branch_id),
                None
            )

            temp_transfer_list = [
                item for item in temp_transfer_list
                if not (
                    item["product_id"] == product_id  # Use product_id
                    and item["batch_number"] == batch_number
                    and item["source_branch_id"] == source_branch_id
                    and item["destination_branch_id"] == destination_branch_id
                )
            ]
            request.session["TEMP_TRANSFER_LIST"] = temp_transfer_list

            if item_to_remove:
                messages.success(request, _("Item removed from the temporary transfer list."))
            else:
                messages.warning(request, _("Item not found in the temporary transfer list."))

        elif "submit_transfer" in request.POST:
            if temp_transfer_list:
                source_branch_ids = {item["source_branch_id"] for item in temp_transfer_list}
                destination_branch_ids = {item["destination_branch_id"] for item in temp_transfer_list}
                if len(source_branch_ids) > 1 or len(destination_branch_ids) > 1:
                    messages.error(request, _("All transfer items must have the same source and destination branches."))
                    return redirect("create-transfer")

                source_branch = Branch.objects.get(id=temp_transfer_list[0]["source_branch_id"])
                destination_branch = Branch.objects.get(id=temp_transfer_list[0]["destination_branch_id"])
                date_transferred = temp_transfer_list[0]["date_transferred"]

                try:
                    worker = request.user.worker_profile
                except AttributeError:
                    messages.error(request, _("You do not have a worker profile. Please contact the administrator."))
                    return redirect("create-transfer")

                stock_transfer = StockTransfer.objects.create(
                    source_branch=source_branch,
                    destination_branch=destination_branch,
                    transferred_by=worker,
                    date_transferred=date_transferred,
                    status="Pending"
                )

                for item in temp_transfer_list:
                    product = Product.objects.filter(id=item["product_id"]).first()  # Use product_id instead of product_code
                    batch_number = item["batch_number"]
                    quantity = item["quantity"]

                    batch = Batch.objects.filter(batch_number=batch_number).first()
                    if not batch:
                        messages.error(request, _(f"Batch {batch_number} not found for product {product.generic_name_dosage}."))
                        stock_transfer.delete()
                        return redirect("create-transfer")

                    # Debug: Log the query details for submission
                    print(f"Submitting transfer - Product ID: {product.id}, "
                          f"Batch: {batch_number} (ID: {batch.id}), "
                          f"Branch: {source_branch.branch_name} (ID: {source_branch.id})")
                    source_stock = Stock.objects.filter(
                        branch=source_branch,
                        product=product,
                        batch=batch
                    ).first()
                    print(f"Source stock result on submit: {source_stock}")

                    # Additional debug if not found
                    if not source_stock:
                        print(f"All stock for Product ID {product.id}: {Stock.objects.filter(product=product).values('branch__branch_name', 'batch__batch_number', 'total_stock')}")
                        print(f"All stock for Batch ID {batch.id}: {Stock.objects.filter(batch=batch).values('branch__branch_name', 'product__product_code', 'total_stock')}")
                        print(f"All stock in Branch ID {source_branch.id}: {Stock.objects.filter(branch=source_branch).values('product__product_code', 'batch__batch_number', 'total_stock')}")

                    if not source_stock or source_stock.total_stock < quantity:
                        messages.error(
                            request,
                            _(f"Insufficient stock in {source_branch.branch_name} for {product.generic_name_dosage} (Batch: {batch_number}). "
                              f"Requested: {quantity}, Available: {source_stock.total_stock if source_stock else 0}")
                        )
                        stock_transfer.delete()
                        return redirect("create-transfer")

                    StockTransferItem.objects.create(
                        transfer=stock_transfer,
                        product=product,
                        batch=batch,
                        quantity=quantity
                    )

                StockTransferAuditLog.objects.create(
                    user=worker,
                    transfer=stock_transfer.transfer_id,
                    source_branch=source_branch.branch_name,
                    destination_branch=destination_branch.branch_name,
                    action="create",
                    details=f"Stock transfer created from {source_branch.branch_name} Branch to {destination_branch.branch_name} Branch"
                )

                del request.session["TEMP_TRANSFER_LIST"]
                messages.success(request, _("Stock transfer submitted successfully."))
                return redirect("transfers")

    view_context = {
        "form": form,
        "temp_transfer_list": temp_transfer_list,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'create_transfer.html', context)


# @login_required
# @transaction.atomic
# def complete_transfer_view(request, transfer_id):
#     transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)
#     if transfer.status != "Pending":
#         messages.error(request, _("This transfer cannot be completed as it is not pending."))
#         return redirect("transfers")

#     if request.method == "POST":
#         try:
#             worker = request.user.worker_profile
#         except AttributeError:
#             messages.error(request, _("You do not have a worker profile. Please contact the administrator."))
#             return redirect("transfers")

#         insufficient_stock = []
#         for item in transfer.items.all():
#             product = item.product
#             quantity = item.quantity
#             source_branch = transfer.source_branch
#             if Stock.objects.filter(branch=source_branch, product=product).first().total_stock < quantity:
#                 insufficient_stock.append(f"{product.generic_name_dosage} (Requested: {quantity}, Available: {source_stock.total_stock})")

#         if insufficient_stock:
#             messages.warning(request, _("Some items have insufficient stock: " + ", ".join(insufficient_stock)))
#             return redirect("transfers")

#         for item in transfer.items.all():
#             product = item.product
#             quantity = item.quantity
#             source_branch = transfer.source_branch
#             destination_branch = transfer.destination_branch

#             source_stock, created = Stock.objects.get_or_create(
#                 branch=source_branch, product=product,
#                 defaults={"total_stock": 0, "quantity": 0}
#             )
#             source_stock.total_stock -= quantity
#             source_stock.quantity_transferred += quantity
#             source_stock.save()

#             dest_stock, created = Stock.objects.get_or_create(
#                 branch=destination_branch, product=product,
#                 defaults={"total_stock": 0, "quantity": 0}
#             )
#             dest_stock.total_stock += quantity
#             dest_stock.quantity += quantity
#             dest_stock.save()

#         transfer.status = "Received"  # Changed from "Completed" to "Received"
#         if not transfer.date_transferred:
#             transfer.date_transferred = timezone.now()
#         transfer.save()

#         messages.success(request, _("Stock transfer completed successfully."))
#         return redirect("transfers")

#     messages.error(request, _("Invalid request."))
#     return redirect("transfers")




@login_required
@transaction.atomic
def complete_transfer_view(request, transfer_id):
    stock_transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)

    if stock_transfer.status != "Pending":
        messages.error(request, _("This transfer cannot be completed as it is not pending."))
        return redirect("transfers")

    transfer_items = stock_transfer.items.all()

    if request.method == "POST":
        form = ActualTransferQuantityForm(request.POST, transfer_items=transfer_items)

        if form.is_valid():
            date_received = form.cleaned_data["date_received"]

            for item in transfer_items:
                product = item.product
                batch = item.batch
                source_branch = stock_transfer.source_branch
                destination_branch = stock_transfer.destination_branch
                actual_quantity = form.cleaned_data.get(f'actual_quantity_{item.id}', 0)

                # Retrieve source branch stock (must exist)
                try:
                    source_stock = Stock.objects.get(product=product, batch=batch, branch=source_branch)
                except Stock.DoesNotExist:
                    messages.error(
                        request,
                        _(f"No stock record found for {product.generic_name_dosage} in {source_branch.branch_name}.")
                    )
                    return redirect("stock_transfer_details", transfer_id=stock_transfer.transfer_id)

                if source_stock.total_stock < item.quantity:
                    messages.error(
                        request,
                        _(f"Insufficient stock in {source_branch.branch_name} for {product.generic_name_dosage}. "
                          f"Required: {item.quantity}, Available: {source_stock.total_stock}")
                    )
                    return redirect("stock_transfer_details", transfer_id=stock_transfer.transfer_id)

                # Retrieve or create destination branch stock
                dest_stock, created = Stock.objects.get_or_create(
                    product=product,
                    batch=batch,
                    branch=destination_branch,
                    defaults={
                        'quantity': 0,  # Initial quantity; will be updated below
                        'total_inventory': 0,
                        'begining_inventory': 0,
                        'fixed_beginning_inventory': 0,
                        'quantity_transferred': 0,
                        'total_sold': 0,
                        'total_stock': 0,
                        'created_by': request.user.worker_profile,
                        'date_added': date_received,
                    }
                )
                print(f"Destination stock for Product ID {product.id}, Batch {batch.batch_number if batch else 'No Batch'} at {destination_branch.branch_name}: {dest_stock}, Created: {created}")

                # Set actual quantity received and date on the item
                item.actual_quantity_received = actual_quantity
                item.date_received = date_received

                # Handle surplus, deficit, or normal case for the original transfer
                if actual_quantity > item.quantity:
                    surplus_quantity = actual_quantity - item.quantity
                    item.surplus = surplus_quantity
                    item.deficit = 0
                    source_stock.quantity_transferred += actual_quantity
                    dest_stock.quantity += actual_quantity
                    StockTransferAuditLog.objects.create(
                        user=request.user.worker_profile,
                        transfer=stock_transfer.transfer_id,
                        source_branch=source_branch.branch_name,
                        destination_branch=destination_branch.branch_name,
                        action="surplus",
                        details=f"Surplus of {surplus_quantity} recorded for {product.generic_name_dosage}. Requested: {item.quantity}, Received: {actual_quantity}"
                    )
                elif actual_quantity < item.quantity:
                    deficit_quantity = item.quantity - actual_quantity
                    if source_stock.quantity_transferred < deficit_quantity:
                        messages.error(
                            request,
                            _(f"Cannot reduce quantity_transferred below 0 for {product.generic_name_dosage} in {source_branch.branch_name}.")
                        )
                        return redirect("stock_transfer_details", transfer_id=stock_transfer.transfer_id)
                    source_stock.quantity_transferred += actual_quantity
                    dest_stock.quantity += actual_quantity
                    item.deficit = deficit_quantity
                    item.surplus = 0
                    StockTransferAuditLog.objects.create(
                        user=request.user.worker_profile,
                        transfer=stock_transfer.transfer_id,
                        source_branch=source_branch.branch_name,
                        destination_branch=destination_branch.branch_name,
                        action="deficit",
                        details=f"Deficit of {deficit_quantity} recorded for {product.generic_name_dosage}. Requested: {item.quantity}, Received: {actual_quantity}"
                    )
                else:
                    source_stock.quantity_transferred += item.quantity
                    dest_stock.quantity += actual_quantity
                    item.surplus = 0
                    item.deficit = 0

                source_stock.save()
                dest_stock.save()
                item.save()

            # Log transfer completion
            StockTransferAuditLog.objects.create(
                user=request.user.worker_profile,
                transfer=stock_transfer.transfer_id,
                source_branch=stock_transfer.source_branch.branch_name,
                destination_branch=stock_transfer.destination_branch.branch_name,
                action="complete",
                details=f"Stock transfer completed with {len(transfer_items)} items on {date_received}"
            )

            # Set the original transfer status to "Received"
            stock_transfer.status = "Received"
            stock_transfer.save()

            messages.success(request, _("Stock transfer completed successfully."))
            return redirect("transfers")

        else:
            messages.error(request, _("Invalid data. Please check the form."))
            return redirect("stock_transfer_details", transfer_id=stock_transfer.transfer_id)

    messages.error(request, _("Invalid request."))
    return redirect("transfers")



@login_required
def RequestAuditLogView(request):
    logs = StockRequestAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "request_logs.html", context)



@login_required
def StockTransferAuditLogView(request):
    """
    View to display all stock transfer audit logs, ordered by timestamp (most recent first).
    """
    logs = StockTransferAuditLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 100)  # Paginate logs with 100 logs per page
    page_number = request.GET.get("page")  # Get the current page number from the request
    paginated_logs = paginator.get_page(page_number)  # Get the page object
    offset = (paginated_logs.number - 1) * paginator.per_page  # Calculate offset for display

    # Create a context dictionary for the view
    view_context = {
        "logs": paginated_logs,
        "offset": offset,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "transfer_logs.html", context)


@login_required
def ManageRequestsView(request):
    # Get the user's worker profile and role
    worker_profile = getattr(request.user, 'worker_profile', None)

    if not worker_profile:
        return HttpResponseForbidden(_("You do not have access to manage stock requests."))

    user_role = worker_profile.role
    stock_requests = StockRequest.objects.all()
    in_transit_stocks = InTransit.objects.none()  # Default to empty

    # Check if the worker has the 'Request Stock' privilege
    can_request_stock = worker_profile.privileges.filter(name="Request Stock").exists()

    # Filter stock requests based on the user's role and privileges
    if user_role == "Marketing Director":
        stock_requests = stock_requests.filter(requested_by=worker_profile)

    elif user_role in ["Secretary", "Stock Manager"]:
        stock_requests = stock_requests.filter(requested_by__branch=worker_profile.branch)

    elif can_request_stock:
        stock_requests = stock_requests.filter(requested_by=worker_profile)

    # Stock Managers should see "In Transit" stock for their branch
    if user_role == "Stock Manager":
        in_transit_stocks = InTransit.objects.filter(
        destination=worker_profile.branch,
        status="In Transit"  # Only show items that are still in transit
    )

    # Get the selected status filter, defaulting to empty (no filter)
    status_filter = request.GET.get('status_filter', '')

    # Apply the status filter if it's provided
    if status_filter:
        stock_requests = stock_requests.filter(status__iexact=status_filter)

    # Order by the most recent pending requests first, then by requested_at
    stock_requests = stock_requests.annotate(
        is_pending=Case(
            When(status__iexact="pending", then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("-is_pending", "-requested_at")

    # Apply pagination after filtering
    paginator = Paginator(stock_requests, 100)
    page_number = request.GET.get('page')
    paginated_request = paginator.get_page(page_number)

    # Prepare the context dictionary
    view_context = {
        "stock_requests": paginated_request,
        "in_transit_stocks": in_transit_stocks,  # Now available in context
        "can_request_stock": can_request_stock,  
    }

    # Initialize template layout and render the page
    context = TemplateLayout.init(request, view_context)
    return render(request, 'requests.html', context)



@login_required
def ManageTransfersView(request):
    worker_profile = getattr(request.user, 'worker_profile', None)
    if not worker_profile:
        return HttpResponseForbidden(_("You do not have access to manage stock transfers."))

    user_role = worker_profile.role
    stock_transfers = StockTransfer.objects.all()
    can_transfer_stock = worker_profile.privileges.filter(name="Transfer Stock").exists()

    if user_role == "Marketing Director":
        stock_transfers = stock_transfers.filter(transferred_by=worker_profile)
    elif user_role in ["Secretary", "Stock Manager"]:
        stock_transfers = stock_transfers.filter(
            Q(source_branch=worker_profile.branch) | 
            Q(destination_branch=worker_profile.branch)
        )
    elif can_transfer_stock:
        stock_transfers = stock_transfers.filter(transferred_by=worker_profile)

    status_filter = request.GET.get('status_filter', '')
    if status_filter:
        stock_transfers = stock_transfers.filter(status__iexact=status_filter)

    stock_transfers = stock_transfers.annotate(
        is_pending=Case(
            When(status__iexact="Pending", then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by("-is_pending", "-date_transferred")

    paginator = Paginator(stock_transfers, 100)
    page_number = request.GET.get('page')
    paginated_transfers = paginator.get_page(page_number)

    view_context = {
        "stock_transfers": paginated_transfers,
        "can_transfer_stock": can_transfer_stock,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'transfers.html', context)




@login_required
def stock_request_details(request, request_id):
    """
    View to get the details of a specific stock request.
    """
    stock_request = get_object_or_404(StockRequest, id=request_id)
    product_details = stock_request.stockrequestproduct_set.all()
    in_transit_items = InTransit.objects.filter(stock_request=stock_request)
    view_context = {
        "stock_request": stock_request,
        "product_details": product_details,
        "in_transit_items": in_transit_items,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'requestDetails.html', context)



@login_required
def stock_transfer_details_view(request, transfer_id):
    stock_transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)
    transfer_items = stock_transfer.items.all()  # Related name from StockTransferItem

    view_context = {
        "stock_transfer": stock_transfer,
        "transfer_items": transfer_items,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'stock_transfer_details.html', context)


@login_required
def stock_request_doc_view(request, request_id):
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

    return render(request, 'stock_requisition.html', context)


@login_required
def transfer_slip_doc_view(request, request_id):
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

    return render(request, 'transfer_slip.html', context)

@login_required
def transfer_slip_doc_view_transfer(request, transfer_id):
    """
    View to get the details of a specific stock transfer and generate a transfer slip.
    """
    stock_transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)
    transfer_items = StockTransferItem.objects.filter(transfer=stock_transfer)

    view_context = {
        "stock_transfer": stock_transfer,
        "transfer_items": transfer_items,
    }

    context = TemplateLayout.init(request, view_context)  # Assuming TemplateLayout is a custom utility

    return render(request, 'transfer_slip_transfer.html', context)

@login_required
def goods_receipt_doc_view(request, request_id):
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

    return render(request, 'receipt_note.html', context)


@login_required
def goods_receipt_doc_view_transfer(request, transfer_id):
    """
    View to get the details of a specific stock transfer and generate a goods receipt note.
    """
    stock_transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)
    transfer_items = StockTransferItem.objects.filter(transfer=stock_transfer)

    view_context = {
        "stock_transfer": stock_transfer,
        "transfer_items": transfer_items,
    }

    context = TemplateLayout.init(request, view_context)  # Assuming TemplateLayout is a custom utility

    return render(request, 'receipt_note_transfer.html', context)


@login_required
def picking_list_doc_view_transfer(request, transfer_id):
    """
    View to get the details of a specific stock transfer and generate a picking list.
    """
    stock_transfer = get_object_or_404(StockTransfer, transfer_id=transfer_id)
    transfer_items = StockTransferItem.objects.filter(transfer=stock_transfer)

    view_context = {
        "stock_transfer": stock_transfer,
        "transfer_items": transfer_items,
    }

    context = TemplateLayout.init(request, view_context)  # Assuming TemplateLayout is a custom utility

    return render(request, 'picking_list_transfer.html', context)


@login_required
@transaction.atomic
def approve_or_decline_request(request, request_id):
    stock_request = get_object_or_404(StockRequest, id=request_id)

    if request.method == "POST":
        action = request.POST.get("action")

        try:
            central_warehouse = Branch.objects.get(branch_type="central")
        except Branch.DoesNotExist:
            messages.error(request, _("Central warehouse not found. Please ensure it exists."))
            return redirect("requests")

        if action == "approve":
            product_details = StockRequestProduct.objects.filter(stock_request=stock_request)
            insufficient_stock = []

            for detail in product_details:
                product = detail.product
                quantity = detail.quantity
                batch = detail.batch

                if not batch:
                    messages.error(request, _(f"Batch not specified for {product.generic_name_dosage}."))
                    return redirect("requests")

                batch_number = batch.batch_number

                # Debug: Log the query details
                print(f"Checking stock - Product: {product.product_code} (ID: {product.id}), Batch: {batch_number} (ID: {batch.id}), Branch: {central_warehouse.branch_name} (ID: {central_warehouse.id})")
                central_stock = central_warehouse.stocks.filter(product=product, batch=batch).first()
                if not central_stock:
                    # Fallback query
                    central_stock = Stock.objects.filter(product=product, branch=central_warehouse, batch=batch).first()
                    print(f"Fallback query result: {central_stock}")
                else:
                    print(f"Manager query result: {central_stock}")

                if not central_stock:
                    messages.error(request, _(f"Stock record for {product.generic_name_dosage} (Batch: {batch_number}) not found in central warehouse."))
                    return redirect("requests")

                if stock_request.request_type in ["Normal", "Deficit"] and central_stock.total_stock < quantity:
                    insufficient_stock.append(
                        f"{product.generic_name_dosage} (Batch: {batch_number}, Requested: {quantity}, Available: {central_stock.total_stock})"
                    )

            if insufficient_stock:
                messages.warning(request, _("Some items have insufficient stock: " + ", ".join(insufficient_stock)))
                return redirect("requests")

            for detail in product_details:
                product = detail.product
                quantity = detail.quantity
                batch = detail.batch
                batch_number = batch.batch_number

                central_stock = Stock.objects.filter(product=product, branch=central_warehouse, batch=batch).first()

                if stock_request.request_type == "Surplus":
                    central_stock.quantity_transferred += quantity
                    # central_stock.total_stock += quantity
                    # central_stock.quantity += quantity
                elif stock_request.request_type == "Deficit":
                    central_stock.quantity_transferred -= quantity
                else:
                    central_stock.total_stock -= quantity
                    central_stock.quantity_transferred += quantity

                central_stock.save()

                if stock_request.request_type == "Normal":
                    InTransit.objects.create(
                        product=product,
                        batch=batch,
                        quantity=quantity,
                        source=central_warehouse.branch_name,
                        destination=stock_request.branch,
                        stock_request=stock_request,
                        created_at=stock_request.requested_at
                    )

            try:
                worker = request.user.worker_profile
                worker_branch = worker.branch.branch_name if worker else "Unknown"
            except AttributeError:
                worker = None
                worker_branch = "Unknown"

            StockRequestAuditLog.objects.create(
                user=worker,
                action=f"{stock_request.request_type} Stock Request Approved",
                request=stock_request.request_number,
                branch=worker_branch,
                details=f"{stock_request.request_type} Stock Request Approved by: {worker}. Batch: {batch_number}",
            )

            

            if stock_request.request_type in ["Surplus", "Deficit"]:
                stock_request.status = "Received"
            else:
                stock_request.status = "Accepted"

            stock_request.save()

            messages.success(request, _("Stock request approved. Stock updated accordingly."))
            return redirect("requests")

        elif action == "decline":
            stock_request.status = "Rejected"
            stock_request.save()

            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None

            StockRequestAuditLog.objects.create(
                user=worker,
                action="Stock Request Rejected",
                request=stock_request.request_number,
                branch=worker.branch.branch_name,
                details=f"Stock Request Declined by: {worker}",
            )

            messages.success(request, _("Stock request declined."))
            return redirect("requests")

    messages.error(request, _("Invalid request."))
    return redirect("requests")







@login_required
def upload_stock_request_document(request, request_id):

    # Get the current worker profile from the logged-in user
    try:
        worker = request.user.worker_profile  # If using OneToOneField in Worker model
    except AttributeError:
        messages.error(request, "You are not assigned as a worker in the system.")
        return redirect('dashboard')  # Redirect to an appropriate page

    stock_request = get_object_or_404(StockRequest, id=request_id)
    documents = StockRequestDocument.objects.filter(stock_request=stock_request)  # Fetch existing documents

    document_id = request.GET.get('document_id')  # Check if editing a document
    document = None

    if document_id:
        document = get_object_or_404(StockRequestDocument, id=document_id, stock_request=stock_request)
        form = StockRequestDocumentForm(instance=document)
    else:
        form = StockRequestDocumentForm()

    if request.method == "POST":
        form = StockRequestDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            new_document_type = form.cleaned_data['document_type']  # Get the selected document type

            # Check if a document of the same type already exists (but allow updates)
            if not document and StockRequestDocument.objects.filter(stock_request=stock_request, document_type=new_document_type).exists():
                messages.warning(request, f"A document of type '{new_document_type}' has already been uploaded.")
            else:
                document = form.save(commit=False)
                document.stock_request = stock_request  # Ensure the document is linked to the stock request

                # Assign the worker who uploaded the document
                document.uploaded_by = worker
                document.save()
                messages.success(request, "Document saved successfully.")
                return redirect('upload_stock_request_document', request_id=stock_request.id)  # Stay on the same page
        else:
            messages.error(request, "Error uploading document. Please check the form.")

    view_context = {
        'form': form,
        'stock_request': stock_request,
        'documents': documents,
        'editing': bool(document),  # Flag to check if editing
        'document': document,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "upload_stock_documents.html", context)


@login_required
def edit_stock_request_document(request, document_id):
    document = get_object_or_404(StockRequestDocument, id=document_id)
    request_id = document.stock_request.id  # Get related stock request

    if request.method == "POST":
        form = StockRequestDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            return redirect('upload_stock_request_document', request_id=request_id)  # Stay on the same page
        else:
            messages.error(request, "Error updating document.")

    else:
        form = StockRequestDocumentForm(instance=document)

    view_context = {'form': form, 'document': document}

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "upload_stock_documents.html", context)



@login_required
def delete_stock_request_document(request, document_id):
    document = get_object_or_404(StockRequestDocument, id=document_id)
    request_id = document.stock_request.id  # Get related stock request
    document.delete()
    messages.success(request, "Document deleted successfully.")
    return redirect('upload_stock_request_document', request_id=request_id)



@login_required
def upload_stock_transfer_document(request, transfer_id):
    """
    View to upload or edit a document for a stock transfer.
    """
    # Get the current worker profile from the logged-in user
    try:
        worker = request.user.worker_profile  # If using OneToOneField in Worker model
    except AttributeError:
        messages.error(request, "You are not assigned as a worker in the system.")
        return redirect('dashboard')  # Redirect to an appropriate page

    stock_transfer = get_object_or_404(StockTransfer, id=transfer_id)
    documents = StockTransferDocument.objects.filter(stock_transfer=stock_transfer)  # Fetch existing documents

    document_id = request.GET.get('document_id')  # Check if editing a document
    document = None

    if document_id:
        document = get_object_or_404(StockTransferDocument, id=document_id, stock_transfer=stock_transfer)
        form = StockTransferDocumentForm(instance=document)
    else:
        form = StockTransferDocumentForm()

    if request.method == "POST":
        form = StockTransferDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            new_document_type = form.cleaned_data['document_type']  # Get the selected document type

            # Check if a document of the same type already exists (but allow updates)
            if not document and StockTransferDocument.objects.filter(stock_transfer=stock_transfer, document_type=new_document_type).exists():
                messages.warning(request, f"A document of type '{new_document_type}' has already been uploaded.")
            else:
                document = form.save(commit=False)
                document.stock_transfer = stock_transfer  # Ensure the document is linked to the stock transfer

                # Assign the worker who uploaded the document
                document.uploaded_by = worker
                document.save()
                messages.success(request, "Document saved successfully.")
                return redirect('upload_stock_transfer_document', transfer_id=stock_transfer.id)  # Stay on the same page
        else:
            messages.error(request, "Error uploading document. Please check the form.")

    view_context = {
        'form': form,
        'stock_transfer': stock_transfer,
        'documents': documents,
        'editing': bool(document),  # Flag to check if editing
        'document': document,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "upload_stock_documents_transfer.html", context)

@login_required
def edit_stock_transfer_document(request, document_id):
    """
    View to edit an existing stock transfer document.
    """
    document = get_object_or_404(StockTransferDocument, id=document_id)
    transfer_id = document.stock_transfer.id  # Get related stock transfer

    if request.method == "POST":
        form = StockTransferDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully.")
            return redirect('upload_stock_transfer_document', transfer_id=transfer_id)  # Stay on the same page
        else:
            messages.error(request, "Error updating document.")

    else:
        form = StockTransferDocumentForm(instance=document)

    view_context = {
        'form': form,
        'document': document,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "upload_stock_documents_transfer.html", context)

@login_required
def delete_stock_transfer_document(request, document_id):
    """
    View to delete a stock transfer document.
    """
    document = get_object_or_404(StockTransferDocument, id=document_id)
    transfer_id = document.stock_transfer.id  # Get related stock transfer
    document.delete()
    messages.success(request, "Document deleted successfully.")
    return redirect('upload_stock_transfer_document', transfer_id=transfer_id)




@login_required
@transaction.atomic
def stock_received(request, request_id):
    stock_request = get_object_or_404(StockRequest, id=request_id)
    in_transit_items = InTransit.objects.filter(stock_request=stock_request)

    if request.method == "POST":
        form = ActualQuantityForm(request.POST, in_transit_items=in_transit_items)

        if form.is_valid():
            surplus_items = []
            deficit_items = []
            # Use form field if available, fallback to POST data
            date_received = form.cleaned_data.get("date_received", request.POST.get("date_received"))

            for transit_item in in_transit_items:
                product = transit_item.product
                batch = transit_item.batch  # Now available from InTransit
                branch = transit_item.destination
                actual_quantity = form.cleaned_data.get(f'actual_quantity_{transit_item.id}', 0)

                # Update branch stock with batch specificity
                branch_stock, created = Stock.objects.get_or_create(
                    product=product,
                    batch=batch,
                    branch=branch,
                    defaults={"quantity": actual_quantity, "total_stock": actual_quantity}
                )
                if not created:
                    branch_stock.quantity += actual_quantity
                    # branch_stock.total_stock += actual_quantity  # Maintain total_stock consistency
                    branch_stock.save()

                # Update InTransit record
                transit_item.actual_quantity_received = actual_quantity
                transit_item.date_received = date_received
                transit_item.status = "Delivered"

                # Calculate surplus or deficit
                requested_quantity = transit_item.quantity
                if actual_quantity > requested_quantity:
                    surplus_quantity = actual_quantity - requested_quantity
                    transit_item.surplus = surplus_quantity
                    transit_item.deficit = 0
                    surplus_items.append((product, batch, surplus_quantity))  # Include batch
                elif actual_quantity < requested_quantity:
                    deficit_quantity = requested_quantity - actual_quantity
                    transit_item.deficit = deficit_quantity
                    transit_item.surplus = 0
                    deficit_items.append((product, batch, deficit_quantity))  # Include batch
                else:
                    transit_item.surplus = 0
                    transit_item.deficit = 0

                transit_item.save()

            # Helper function to create surplus/deficit requests with batch
            def create_stock_request(request_type, items):
                new_request = StockRequest.objects.create(
                    branch=stock_request.branch,
                    requested_by=stock_request.requested_by,
                    requested_at=timezone.now(),
                    status="Pending",
                    request_type=request_type
                )
                for product, batch, quantity in items:
                    StockRequestProduct.objects.create(
                        stock_request=new_request,
                        product=product,
                        batch=batch,  # Include batch in new StockRequestProduct
                        quantity=quantity
                    )
                new_request.save()

                try:
                    worker = request.user.worker_profile
                    worker_branch = worker.branch.branch_name if worker else "Unknown"
                except AttributeError:
                    worker = None
                    worker_branch = "Unknown"

                StockRequestAuditLog.objects.create(
                    user=worker,
                    action=f"{request_type} Stock Request Created",
                    request=new_request.request_number,
                    branch=worker_branch,
                    details=f"{request_type} stock request created by: {worker}",
                )

            # Create surplus/deficit requests if applicable
            if surplus_items:
                create_stock_request("Surplus", surplus_items)
                messages.warning(request, _("A new SURPLUS stock request has been created and marked as Pending."))
            if deficit_items:
                create_stock_request("Deficit", deficit_items)
                messages.warning(request, _("A new DEFICIT stock request has been created and marked as Pending."))

            # Mark original request as received
            stock_request.status = "Received"
            stock_request.save()

            messages.success(request, _("Stock received and updated successfully."))
            return redirect("stock")

        else:
            messages.error(request, _("Invalid data. Please check the form."))
            return redirect("stock")

    messages.error(request, _("Invalid request method."))
    return redirect("stock")







@login_required
def stocks_in_transit(request):
    worker = getattr(request.user, 'worker_profile', None)

    # Superusers bypass all restrictions
    if request.user.is_superuser:
        stocks_in_transit = StockRequest.objects.filter(status="Accepted")
        in_transit_items = InTransit.objects.filter(status="In Transit")
    else:
        # Non-superusers must be workers with a branch
        if not worker or not worker.branch:
            return HttpResponseForbidden(_("You do not have access to view stocks in transit."))

        branch = worker.branch

        # Filter StockRequests from this branch OR InTransit items destined for this branch
        stocks_in_transit = StockRequest.objects.filter(
            status="Accepted",
            requested_by__branch=branch  # Requests made by someone from this branch
        )
        in_transit_items = InTransit.objects.filter(
            destination=branch,  # Items coming TO this branch
            status="In Transit"
        )

    view_context = {
        'stocks_in_transit': stocks_in_transit,
        'in_transit_items': in_transit_items,
        'branch_name': getattr(worker.branch, 'branch_name', 'All Branches') if worker else 'All Branches',
        'is_superuser': request.user.is_superuser,  # Pass superuser status to template
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'transit-requests.html', context)


from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden

@login_required
def stocks_movement(request):
    worker = getattr(request.user, 'worker_profile', None)

    if not worker or not worker.branch:
        return HttpResponseForbidden(_("You do not have access to view stocks in transit."))

    branch = worker.branch
    stocks_in_transit = InTransit.objects.select_related("stock_request").all()

    # Get search parameters
    search_query = request.GET.get("search_query", "").strip()
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    status_filter = request.GET.get("status")

    # Filter by date range if both start and end dates are provided
    if start_date and end_date:
        stocks_in_transit = stocks_in_transit.filter(created_at__date__range=[start_date, end_date])

    # Filter by status
    if status_filter:
        stocks_in_transit = stocks_in_transit.filter(status=status_filter)

    # Apply search filtering across different models
    if search_query:
        stocks_in_transit = stocks_in_transit.filter(
            Q(product__generic_name_dosage__generic_name__icontains=search_query) |  # Generic Name Dosage
            Q(product__brand_name__generic_name__icontains=search_query) |  # Brand Name
            Q(product__batch__batch_number__icontains=search_query) |  # Batch Number
            Q(product__batch__generic_name__generic_name__icontains=search_query) |  # Batch Generic Name
            Q(stock_request__request_number__icontains=search_query) |  # Stock Request Number
            Q(stock_request__status__icontains=search_query) |  # Stock Request Status
            Q(stock_request__branch__branch_name__icontains=search_query)  # Branch Name
        )

    # Order by most recent
    stocks_in_transit = stocks_in_transit.order_by("-created_at")

    # Pagination
    paginator = Paginator(stocks_in_transit, 100)
    page_number = request.GET.get("page")
    paginated_stocks = paginator.get_page(page_number)

    # Calculate differences
    stock_differences = [
        {
            "stock": stock,
            "difference": (stock.actual_quantity_received - stock.quantity) if stock.actual_quantity_received is not None else None,
            "request_type": (
                "Deficit" if (stock.actual_quantity_received is not None and stock.actual_quantity_received < stock.quantity) else
                "Surplus" if (stock.actual_quantity_received is not None and stock.actual_quantity_received > stock.quantity) else
                "Normal"
            )
        }
        for stock in paginated_stocks
    ]

    view_context = {
        "stock_differences": stock_differences,
        "stocks_in_transit": paginated_stocks,
        "branch_name": branch.branch_name,
        "search_query": search_query,
        "start_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "stock_movement.html", context)





@login_required
def stocks_received_list(request):
    """
    View to display stock requests with status "Received".
    - Superusers can see all stock requests with status "Received".
    - Non-superusers can only see stock requests for their branch.
    """
    # Get the worker profile of the logged-in user
    worker = getattr(request.user, 'worker_profile', None)

    # If the user is not a worker or doesn't belong to a branch (and is not a superuser), deny access
    if not request.user.is_superuser and (not worker or not worker.branch):
        return HttpResponseForbidden(_("You do not have access to view received stocks."))

    # Retrieve stock requests with status "Received"
    if request.user.is_superuser:
    # Get all delivered InTransit records
        stocks_received = InTransit.objects.filter(status="Delivered").select_related('stock_request', 'destination')
    else:
        # Filter by the branch of the logged-in worker
        branch = worker.branch
        stocks_received = InTransit.objects.filter(destination=branch, status="Delivered").select_related('stock_request', 'destination')


    view_context = {
        'stocks_received': stocks_received,
        'is_superuser': request.user.is_superuser,  # Pass whether the user is a superuser to the template
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, 'stock_received_list.html', context)


def generate_picking_list(stock_request):
    # Create a BytesIO buffer
    buffer = io.BytesIO()

    # Create a PDF canvas
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Picking List for Request #{stock_request.id}")

    # Add a logo (replace with the actual path to your logo)
    logo_path = "apps/gcpharma.jpg"  # Update with your logo file path
    try:
        pdf.drawImage(logo_path, 250, 780, width=100, height=50)  # Center the logo at the top
    except:
        pdf.drawString(250, 790, "LOGO PLACEHOLDER")  # Placeholder if logo not found

    # Header text
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(300, 750, f"Picking List for Stock Request #{stock_request.id}")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 720, f"Requested by: {stock_request.requested_by}")
    pdf.drawString(50, 700, f"Requested at: {stock_request.requested_at.strftime('%Y-%m-%d %H:%M')}")

    # Add a styled table for the products
    data = [["Generic Name", "Quantity"]]  # Table header
    for product_detail in stock_request.stockrequestproduct_set.all():
        data.append([
            str(product_detail.product.generic_name_dosage),
            str(product_detail.quantity),
        ])

    # Create the table
    table = Table(data, colWidths=[3.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.darkblue),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ]))

    # Calculate table position to center it
    table_width, table_height = table.wrap(450, 400)
    x_position = (A4[0] - table_width) / 2
    y_position = 600 - table_height  # Adjusted to reduce space between table and header
    table.drawOn(pdf, x_position, y_position)

    # Footer text
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(50, 50, "This document was automatically generated.")
    pdf.drawString(50, 35, f"Tracking ID: {stock_request.id}")

    # Finalize PDF
    pdf.showPage()
    pdf.save()

    # Save the PDF to a FileField or return it as a response
    buffer.seek(0)
    return buffer


def save_picking_list(stock_request):
    buffer = generate_picking_list(stock_request)
    stock_request.picking_list.save(f"picking_list_{stock_request.id}.pdf", File(buffer))
    buffer.close()
