from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import PackSize
from .forms import PackSizeForm
from django.contrib import messages

# Create your views here.
def ManagePackView(request):
    pack_size = PackSize.objects.all()

    # Create a new context dictionary for this view 
    view_context = {
        "pack_size": pack_size,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_packsize.html', context)


def add_pack_view(request):
    
    pack_size = PackSize.objects.all()
    
    if request.method == "POST":
        form = PackSizeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pack Size added successfully!")
            return redirect('add-packsize')
    else:
        form = PackSizeForm()
    view_context = {
        "form": form,
        "pack_size": pack_size,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_packsize.html', context)

def edit_pack_view(request, pk):
    pack_size = get_object_or_404(PackSize, pk=pk)  
    
    if request.method == "POST":
        form = PackSizeForm(request.POST, instance=pack_size)  
        if form.is_valid():
            form.save()
            messages.success(request, "Pack Size updated successfully!")
            return redirect('add-packsize')  
    else:
        form = PackSizeForm(instance=pack_size)  

    pack_size = PackSize.objects.all()  

    view_context = {
        "form": form,
        "pack_size": pack_size,
        "is_editing": True,  
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_packsize.html', context)


def delete_pack_view(request, pk):
    pack_size = get_object_or_404(PackSize, pk=pk)  # Get the batch by ID
    if request.method == "POST":
        pack_size.delete()  # Delete the batch
        messages.success(request, "Pack Size deleted successfully!")
        return redirect('add-packsize')  # Redirect to the batch list

    pack_size = PackSize.objects.all()

    view_context = {
        "pack_size": pack_size,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_packsize.html', context)