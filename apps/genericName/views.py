from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import GenericName
from .forms import BrandForm

# Create your views here.
def ManageGenericView(request):
    genericName = GenericName.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "genericName": genericName,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)


def add_generic_view(request):
    
    genericName = GenericName.objects.all()
    
    if request.method == "POST":
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('add-genericName')
    else:
        form = BrandForm()
    view_context = {
        "form": form,
        "genericName": genericName,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)

def edit_generic_view(request, pk):
    genericName = get_object_or_404(GenericName, pk=pk)  
    
    if request.method == "POST":
        form = BrandForm(request.POST, instance=genericName)  
        if form.is_valid():
            form.save()
            return redirect('add-genericName')  
    else:
        form = BrandForm(instance=genericName)  

    genericName = GenericName.objects.all()  

    view_context = {
        "form": form,
        "genericName": genericName,
        "is_editing": True,  
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)


def delete_generic_view(request, pk):
    generic_name = get_object_or_404(GenericName, pk=pk)  # Get the batch by ID
    if request.method == "POST":
        generic_name.delete()  # Delete the batch
        return redirect('add-genericName')  # Redirect to the batch list

    generic_name = GenericName.objects.all()

    view_context = {
        "generic_name": generic_name,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_genericName.html', context)