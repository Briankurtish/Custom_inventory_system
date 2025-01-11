from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from .models import Batch, Product
from .forms import AddProductForm, BatchForm, EditProductForm, ProductForm, UpdateProductForm
from apps.genericName.models import GenericName
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator



"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


@login_required
def ManageProductView(request):
    products = Product.objects.all()
    batches = Batch.objects.all()

    paginator = Paginator(products, 10) 
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_products = paginator.get_page(page_number)
    
    # Create a new context dictionary for this view 
    view_context = {
        "products": paginated_products,
        "batches": batches,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'product.html', context)



@login_required
def ManageBatchView(request):
    batch = Batch.objects.all()  # Fetch all batches
    
    # Handle form submission
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()  # Save the batch object
            return redirect('add-batch')  # Redirect after successful form submission
    else:
        form = BatchForm()  # Create an empty form instance for GET request
    
    # Create a context to pass to the template
    view_context = {
        "batch": batch,
        "form": form,  # Pass the form to the template
    }
    
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_batchNumber.html', context)


@login_required
def add_batch_view(request):
    
    batches = Batch.objects.all()
    
    if request.method == "POST":
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add-batch')
    else:
        form = BatchForm()
    view_context = {
        "form": form,
        "batches": batches,
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
def add_product_view(request):
    if request.method == "POST":
        form = AddProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.unit_price = 0.00  # Default price for new products
            product.save()
            return redirect('products')
    else:
        form = AddProductForm()

    view_context = {
        "form": form,
        "is_editing": False,  # Flag for add operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addProduct.html', context)


@login_required
def edit_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = EditProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
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
    product = get_object_or_404(Product, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = UpdateProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.unit_price = form.cleaned_data['unit_price']  # Update price
            product.save()
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
    """
    Handles deleting a crypto wallet.
    """
    product = get_object_or_404(Product, id=pk)
    if request.method == "POST":
        product.delete()
        return redirect("products")

    view_context = {
        "product": product,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteProduct.html', context)


@login_required
def edit_batch_view(request, pk):
    batch = get_object_or_404(Batch, pk=pk)  
    
    if request.method == "POST":
        form = BatchForm(request.POST, instance=batch)  
        if form.is_valid():
            form.save()
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
    if request.method == "POST":
        batch.delete()  # Delete the batch
        return redirect('add-batch')  # Redirect to the batch list

    batch = Batch.objects.all()

    view_context = {
        "batch": batch,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteBatch.html', context)