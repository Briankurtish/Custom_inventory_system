from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Branch
from .forms import BranchForm


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageBranchView(request):
    branch = Branch.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "branch": branch,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'branches.html', context)

def add_branch_view(request, pk=None):
    # branches = Branch.objects.all() 
    
    if pk:
        branch = get_object_or_404(Branch, pk=pk)  
        form = BranchForm(request.POST or None, instance=branch) 
    else:
        product = None
        form = BranchForm(request.POST or None)  

    # Handle the POST request (form submission)
    if request.method == "POST":
        if form.is_valid():
            form.save()  # Save the product (create or update based on `pk`)
            return redirect('branches')  # Redirect to the product list after saving

    view_context = {
        "form": form,
        "is_editing": bool(pk),  # Flag to indicate if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addBranch.html', context)

def update_branch_view(request, pk):
    branch = get_object_or_404(Branch, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)  # Bind form to the product instance
        if form.is_valid():
            form.save()
            return redirect('branches')  # Redirect to the product list
    else:
        form = BranchForm(instance=branch)

    branches = Branch.objects.all()

    view_context = {
        "form": form,
        "branches": branches,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addBranch.html', context)

def delete_branch_view(request, pk):
    """
    Handles deleting a crypto wallet.
    """
    branch = get_object_or_404(Branch, id=pk)
    if request.method == "POST":
        branch.delete()
        return redirect("branches")

    view_context = {
        "branch": branch,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteBranch.html', context)