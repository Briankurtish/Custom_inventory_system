from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Worker
from .forms import UserCreationForm, WorkerForm


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageWorkerView(request):
    worker = Worker.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "worker": worker,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'workers.html', context)


def add_worker_view(request, pk=None):
    
    if pk:
        worker = get_object_or_404(Worker, pk=pk)  # Fetch the product for editing
        form = UserCreationForm(request.POST or None, instance=worker)  # Bind the form to the existing product
    else:
        worker = None
        form = UserCreationForm(request.POST or None)  # Empty form for creating a new product

    # Handle the POST request (form submission)
    if request.method == "POST":
        if form.is_valid():
            form.save()  # Save the product (create or update based on `pk`)
            return redirect('workers')  # Redirect to the product list after saving

    view_context = {
        "form": form,
        "is_editing": bool(pk),  # Flag to indicate if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addWorker.html', context)


def update_worker_view(request, pk):
    worker = get_object_or_404(Worker, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = WorkerForm(request.POST, instance=worker)  # Bind form to the product instance
        if form.is_valid():
            form.save()
            return redirect('workers')  # Redirect to the product list
    else:
        form = WorkerForm(instance=worker)
    
    view_context = {
        "form": form,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addWorker.html', context)