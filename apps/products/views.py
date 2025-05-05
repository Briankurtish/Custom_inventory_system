from django.views.generic import TemplateView
from apps.oldinvoice.models import OldInvoiceOrderItem
from apps.orders.models import PurchaseOrderItem
from web_project import TemplateLayout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from .models import Batch, BatchAuditLog, DosageForm, DosageType, Product, ProductAuditLog
from .forms import AddProductForm, BatchForm, DosageFormForm, DosageTypeForm, EditProductForm, ProductForm, UpdateProductForm
from apps.genericName.models import GenericName
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
import csv




"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""



@login_required
def ManageProductView(request):
    search_query = request.GET.get("search_query", "").strip()

    # Fetch all products and order them by generic name
    products = Product.objects.all().order_by("generic_name_dosage__generic_name")

    # Apply search filtering
    if search_query:
        products = products.filter(
            Q(product_code__icontains=search_query) |
            Q(brand_name__brand_name__icontains=search_query) |  # Corrected this line
            Q(generic_name_dosage__generic_name__icontains=search_query) |
            Q(dosage_form__name__icontains=search_query) |
            Q(dosage_type__name__icontains=search_query) |
            Q(batch__batch_number__icontains=search_query)
        ).order_by("generic_name_dosage__generic_name")


    batches = Batch.objects.all()

    # Paginate the filtered queryset
    paginator = Paginator(products, 100)
    page_number = request.GET.get("page")
    paginated_products = paginator.get_page(page_number)

    offset = (paginated_products.number - 1) * paginator.per_page

    # Create a new context dictionary for this view
    view_context = {
        "products": paginated_products,
        "batches": batches,
        "offset": offset,  # Pass the offset to the template
        "search_query": search_query,  # Pass the search query to retain input
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, "product.html", context)




@login_required
def ManageBatchView(request):
    search_query = request.GET.get("search_query", "").strip()

    # Fetch all batches and order them by generic name
    batches = Batch.objects.all().order_by("generic_name__generic_name")

    # Apply search filtering
    if search_query:
        batches = batches.filter(
            Q(batch_number__icontains=search_query) |
            Q(generic_name__generic_name__icontains=search_query) |
            Q(bl_number__icontains=search_query)
        ).order_by("generic_name__generic_name")

    # Paginate the results
    paginator = Paginator(batches, 100)  # Adjust per-page count as needed
    page_number = request.GET.get("page")
    paginated_batches = paginator.get_page(page_number)

    # Handle form submission
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add-batch')
    else:
        form = BatchForm()

    view_context = {
        "batches": paginated_batches,
        "products": Product.objects.all(),
        "form": form,
        "search_query": search_query,  # Pass search query to the template
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, 'add_batchNumber.html', context)


@login_required
def BatchAuditLogView(request):
    logs = BatchAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "batch_logs.html", context)


@login_required
def ProductAuditLogView(request):
    logs = ProductAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "product_logs.html", context)


@login_required
def add_batch_view(request, pk=None):
    search_query = request.GET.get("search_query", "").strip()

    # Fetch all batches and order them by generic name
    batches = Batch.objects.all().order_by("generic_name__generic_name")

    # Apply search filtering
    if search_query:
        batches = batches.filter(
            Q(batch_number__icontains=search_query) |
            Q(generic_name__generic_name__icontains=search_query) |
            Q(bl_number__icontains=search_query)
        ).order_by("generic_name__generic_name")

    # Paginate the results
    paginator = Paginator(batches, 100)  # Adjust per-page count as needed
    page_number = request.GET.get("page")
    paginated_batches = paginator.get_page(page_number)

    # Handle form submission (Edit / Create)
    if pk:
        batch = get_object_or_404(Batch, pk=pk)
        form = BatchForm(request.POST or None, instance=batch)
        action = "update"
    else:
        batch = None
        form = BatchForm(request.POST or None)
        action = "create"

    if request.method == "POST":
        if form.is_valid():
            batch = form.save(commit=False)

            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None

            if action == "create" and worker:
                batch.batch_created_by = worker

            batch.save()

            # Log the action
            log_details = f"Batch {action}d by {'admin' if worker is None else worker}."
            BatchAuditLog.objects.create(
                user=worker,
                batch_number=batch.batch_number,
                action=action,
                details=log_details
            )

            messages.success(
                request, _("Batch {action}d successfully!".format(action=action))
            )
            return redirect('batches')

    view_context = {
        "form": form,
        "batch": batch,
        "batches": paginated_batches,
        "search_query": search_query,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_batchNumber.html', context)




@login_required
def get_brand_name(request, generic_name_id):
    try:
        # Get the GenericName object
        generic_name = GenericName.objects.get(id=generic_name_id)

        # Return the brand_name as JSON
        brand_name = generic_name.brand_name or ''  # Return an empty string if no brand_name is set
        return JsonResponse({'brand_name': brand_name})

    except GenericName.DoesNotExist:
        return JsonResponse({'brand_name': ''}, status=404)


@login_required
def fetch_brand_names(request):
    generic_name_id = request.GET.get("generic_name_id")
    if generic_name_id:
        # Get all brand names associated with the selected generic name
        brand_names = GenericName.objects.filter(id=generic_name_id).values("id", "brand_name")
        return JsonResponse({"brand_names": list(brand_names)})
    return JsonResponse({"brand_names": []})



@login_required
def add_product_view(request):
    if request.method == "POST":
        form = AddProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.unit_price = 0.00  # Default price for new products

            # Log the action
            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None

            if worker:
                product.created_by = worker

            product.save()

            ProductAuditLog.objects.create(
                user=worker,
                generic_name=product.generic_name_dosage,
                action="create",
                details=f"Product '{product.generic_name_dosage}' added by {'admin' if worker is None else worker}."
            )

            messages.success(request, _("Product added successfully!"))
            return redirect('products')
    else:
        form = AddProductForm()

    view_context = {
        "form": form,
        "is_editing": False,  # Flag for add operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addProduct.html', context)


def product_transaction_history(request, product_id):
    # Fetch the product
    product = get_object_or_404(Product, id=product_id)

    # Get sales history from OldInvoiceOrderItem
    sales_history = OldInvoiceOrderItem.objects.filter(product=product).select_related('invoice_order')

    # Get purchase history from PurchaseOrderItem
    purchase_history = PurchaseOrderItem.objects.filter(stock__product=product).select_related('purchase_order')

    view_context = {
        "product": product,
        "sales_history": sales_history,
        "purchase_history": purchase_history,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, "productTransactionHistory.html", context)



def get_brand_and_batches(request, generic_name_id):
    try:
        # Fetch the GenericName object based on the selected generic_name_id
        generic_name = get_object_or_404(GenericName, id=generic_name_id)

        # Fetch the related brand names
        brand_names = GenericName.objects.filter(generic_name=generic_name.generic_name).values_list('brand_name', flat=True).distinct()

        # Fetch the related batch numbers
        batches = Batch.objects.filter(generic_name=generic_name).values_list('batch_number', flat=True).distinct()

        # Return the brand names and batches as a JSON response
        return JsonResponse({
            "brand_names": list(brand_names),
            "batches": list(batches)
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




@login_required
def edit_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = EditProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()

            # Log the action
            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None

            ProductAuditLog.objects.create(
                user=worker,
                generic_name=product.generic_name_dosage,
                action="update",
                details=f"Product '{product.generic_name_dosage}' updated by {'admin' if worker is None else worker}."
            )

            messages.success(request, _("Product updated successfully!"))
            return redirect('products')
    else:
        form = EditProductForm(instance=product)

    view_context = {
        "form": form,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addProduct.html', context)


@login_required
def update_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = UpdateProductForm(request.POST, instance=product)
        if form.is_valid():
            old_price = product.unit_price
            product = form.save(commit=False)
            product.unit_price = form.cleaned_data['unit_price']
            product.save()

            # Log the action
            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None

            ProductAuditLog.objects.create(
                user=worker,
                generic_name=product.generic_name_dosage,
                action="update_price",
                details=f"Product '{product.generic_name_dosage}' price updated from {old_price} to {product.unit_price} by {'admin' if worker is None else worker}."
            )

            messages.success(request, _("Product price updated successfully!"))
            return redirect('products')
    else:
        form = UpdateProductForm(instance=product)

    view_context = {
        "form": form,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addProduct.html', context)


@login_required
def delete_product_view(request, pk):
    product = get_object_or_404(Product, id=pk)

    if request.method == "POST":
        # Log the delete action before deleting the product
        try:
            worker = request.user.worker_profile
        except AttributeError:
            worker = None

        ProductAuditLog.objects.create(
            user=worker,
            generic_name=product.generic_name_dosage,
            action="delete",
            details=f"Product '{product.generic_name_dosage}' deleted by {'admin' if worker is None else worker}."
        )

        product.delete()
        messages.success(request, _("Product deleted successfully!"))
        return redirect("products")

    view_context = {
        "product": product,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteProduct.html', context)


from django.utils.timezone import now

@login_required
def edit_batch_view(request, pk):
    batch = get_object_or_404(Batch, pk=pk)

    if request.method == "POST":
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            updated_batch = form.save()

            # Log the update action
            try:
                worker = request.user.worker_profile
            except AttributeError:
                worker = None  # Handle case where no worker profile exists

            log_details = f"Batch '{updated_batch.batch_number}' updated by {'admin' if worker is None else worker}."
            BatchAuditLog.objects.create(
                user=worker,
                batch_number=updated_batch.batch_number,
                action="update",
                details=log_details,
                timestamp=now(),
            )

            messages.success(request, _("Batch edited successfully!"))
            return redirect('add-batch')
    else:
        form = BatchForm(instance=batch)

    batches = Batch.objects.all()

    view_context = {
        "form": form,
        "batches": batches,
        "is_editing": True,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_batchNumber.html', context)


@login_required
def delete_batch_view(request, pk):
    batch = get_object_or_404(Batch, pk=pk)  # Get the batch by ID
    batch_number = batch.batch_number  # Capture the batch name before deletion

    if request.method == "POST":
        try:
            worker = request.user.worker_profile
        except AttributeError:
            worker = None  # Handle case where no worker profile exists

        # Log the delete action
        log_details = f"Batch '{batch_number}' deleted by {'admin' if worker is None else worker}."
        BatchAuditLog.objects.create(
            user=worker,
            batch_number=batch_number,
            action="delete",
            details=log_details,
            timestamp=now(),
        )

        batch.delete()  # Delete the batch
        messages.success(request, _("Batch deleted successfully!"))
        return redirect('add-batch')  # Redirect to the batch list

    batches = Batch.objects.all()

    view_context = {
        "batch": batch,
        "batches": batches,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteBatch.html', context)



@login_required
def add_dosage_form_view(request, pk=None):
    dosage_form = DosageForm.objects.all()

    if pk:
        dosage_form = get_object_or_404(DosageForm, pk=pk)  # Fetch the specific batch if editing
        form = DosageFormForm(request.POST or None, instance=dosage_form)
        action = "update"
    else:
        dosage_form = None
        form = DosageFormForm(request.POST or None)
        action = "create"

    if request.method == "POST":
        if form.is_valid():
            dosage_form = form.save()
            messages.success(
                request, _("Dosage Form {action}d successfully!".format(action=action))
            )
            return redirect('add-dosage-form')
    all_dosage_form = DosageForm.objects.all()

    view_context = {
        "form": form,
        "dosage_form": all_dosage_form,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_dosageForm.html', context)


@login_required
def edit_dosage_form_view(request, pk):
    dosage_form = get_object_or_404(DosageForm, pk=pk)

    if request.method == "POST":
        form = DosageFormForm(request.POST, instance=dosage_form)
        if form.is_valid():
            dosage_form = form.save()

            messages.success(request, _("Dosage Form edited successfully!"))
            return redirect('add-dosage-form')
    else:
        form = DosageFormForm(instance=dosage_form)

    all_dosage_form = DosageForm.objects.all()

    view_context = {
        "form": form,
        "dosage_form": all_dosage_form,
        "is_editing": True,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_dosageForm.html', context)


@login_required
def delete_dosage_form_view(request, pk):
    dosage_form = get_object_or_404(DosageForm, pk=pk)  # Get the batch by ID

    if request.method == "POST":
        dosage_form.delete()  # Delete the batch
        messages.success(request, _("Dosage Form deleted successfully!"))
        return redirect('add-dosage-form')  # Redirect to the batch list

    all_dosage_form = DosageForm.objects.all()

    view_context = {
        "dosage_form": all_dosage_form,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteDosageForm.html', context)




@login_required
def add_dosage_type_view(request, pk=None):
    dosage_type = DosageType.objects.all()

    if pk:
        dosage_type = get_object_or_404(DosageType, pk=pk)  # Fetch the specific batch if editing
        form = DosageTypeForm(request.POST or None, instance=dosage_type)
        action = "update"
    else:
        dosage_type = None
        form = DosageTypeForm(request.POST or None)
        action = "create"

    if request.method == "POST":
        if form.is_valid():
            dosage_type = form.save()
            messages.success(
                request, _("Dosage Type {action}d successfully!".format(action=action))
            )
            return redirect('add-dosage-type')

    all_dosage_type = DosageType.objects.select_related('dosage_form').all()

    view_context = {
        "form": form,
        "dosage_types": all_dosage_type,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_dosageType.html', context)


@login_required
def edit_dosage_type_view(request, pk):
    dosage_type = get_object_or_404(DosageType, pk=pk)

    if request.method == "POST":
        form = DosageTypeForm(request.POST, instance=dosage_type)
        if form.is_valid():
            dosage_type = form.save()

            messages.success(request, _("Dosage Type edited successfully!"))
            return redirect('add-dosage-type')
    else:
        form = DosageTypeForm(instance=dosage_type)

    all_dosage_type = DosageType.objects.all()

    view_context = {
        "form": form,
        "dosage_types": all_dosage_type,
        "is_editing": True,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_dosageType.html', context)


@login_required
def delete_dosage_type_view(request, pk):
    dosage_type = get_object_or_404(DosageType, pk=pk)  # Get the batch by ID

    if request.method == "POST":
        dosage_type.delete()  # Delete the batch
        messages.success(request, _("Dosage Type deleted successfully!"))
        return redirect('add-dosage-type')  # Redirect to the batch list

    all_dosage_type = DosageType.objects.all()

    view_context = {
        "dosage_types": all_dosage_type,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteDosageType.html', context)



def get_dosage_types(request):
    dosage_form_id = request.GET.get('dosage_form_id')
    dosage_types = DosageType.objects.filter(dosage_form_id=dosage_form_id)
    data = [{"id": dt.id, "name": dt.name} for dt in dosage_types]
    return JsonResponse(data, safe=False)



@login_required
def product_list_report(request):
    # Fetch all products with related fields
    products = Product.objects.all().select_related(
        'brand_name', 'generic_name_dosage', 'dosage_form', 'pack_size', 'batch'
    )

    # Handle CSV export
    if 'export' in request.GET and request.GET['export'] == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"product_list_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        # Write headers
        writer.writerow([
            'Product Code', 'Brand Name', 'Generic Name', 'Dosage Form',
            'Pack Size', 'Batch Number', 'Expiry Date'
        ])

        # Write data
        for product in products:
            writer.writerow([
                product.product_code or 'N/A',
                product.brand_name.brand_name if product.brand_name else 'N/A',
                product.generic_name_dosage.generic_name if product.generic_name_dosage else 'N/A',
                product.dosage_form.name if product.dosage_form else 'N/A',
                product.pack_size if product.pack_size else 'N/A',  # Assuming PackSize has a 'size' field
                product.batch.batch_number if product.batch else 'N/A',
                product.batch.expiry_date.strftime('%d %b %Y') if product.batch and product.batch.expiry_date else 'N/A'
            ])

        return response

    # Prepare context for HTML rendering
    context = {
        'products': products,
        'current_date_time': timezone.now(),
    }

    return render(request, 'product_list_report.html', context)



@login_required
def product_price_list_report(request):
    # Fetch all products with related fields
    products = Product.objects.all().select_related(
        'brand_name', 'generic_name_dosage', 'dosage_form', 'pack_size', 'batch'
    )

    # Handle CSV export
    if 'export' in request.GET and request.GET['export'] == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"product_price_list_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        # Write headers
        writer.writerow([
            'Product Code', 'Brand Name', 'Generic Name', 'Dosage Form',
            'Pack Size', 'Batch Number', 'Expiry Date', 'Unit Price'
        ])

        # Write data
        for product in products:
            writer.writerow([
                product.product_code or 'N/A',
                product.brand_name.brand_name if product.brand_name else 'N/A',
                product.generic_name_dosage.generic_name if product.generic_name_dosage else 'N/A',
                product.dosage_form.name if product.dosage_form else 'N/A',
                product.pack_size if product.pack_size else 'N/A',  # Assuming PackSize has a 'size' field
                product.batch.batch_number if product.batch else 'N/A',
                product.batch.expiry_date.strftime('%d %b %Y') if product.batch and product.batch.expiry_date else 'N/A',
                product.unit_price if product.unit_price else 'N/A'
            ])

        return response

    # Prepare context for HTML rendering
    context = {
        'products': products,
        'current_date_time': timezone.now(),
    }

    return render(request, 'product_price_list_report.html', context)
