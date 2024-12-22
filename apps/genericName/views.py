from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import GenericName
from django.contrib import messages
from .forms import GenericNameForm

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



def add_generic_name(request):
    # Fetch all generic names from the database
    generic_names = GenericName.objects.all()

    if request.method == "POST":
        form = GenericNameForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Generic name added successfully!")
            return redirect("add-genericName")  # Replace with your desired redirect URL
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = GenericNameForm()

    view_context = {
        "form": form,
        "generic_names": generic_names,  # Pass the list of generic names to the template
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    # Render the page with the updated context
    return render(request, 'add_genericName.html', context)

def edit_generic_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    generic_name = get_object_or_404(GenericName, pk=pk)
    generic_names = GenericName.objects.all()
    
    
    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = GenericNameForm(request.POST, instance=generic_name)
        if form.is_valid():
            form.save()
            messages.success(request, "Generic name updated successfully!")
            return redirect('add-genericName')  # Redirect to the appropriate page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Populate the form with existing data for GET requests
        form = GenericNameForm(instance=generic_name)

    # Fetch all generic names for display (if needed)
    all_generic_names = GenericName.objects.all()

    view_context = {
        "form": form,
        "generic_names": generic_names,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)


def delete_generic_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    generic_name = get_object_or_404(GenericName, pk=pk)
    
    if request.method == "POST":
        # Delete the instance on POST
        generic_name.delete()
        messages.success(request, "Generic name deleted successfully!")
        return redirect('add-genericName')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_generic_names = GenericName.objects.all()

    view_context = {
        "genericName": all_generic_names,  # To display the list of generic names
        "item_to_delete": generic_name,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_genericName.html', context)