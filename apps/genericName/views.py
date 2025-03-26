from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import GenericName, GenericNameAuditLog
from django.contrib import messages
from .forms import GenericNameForm
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q



@login_required
def ManageGenericView(request):

    # Fetch all generic names
    generic_names = GenericName.objects.all()
    # Order by alphabetical order
    generic_names = generic_names.order_by("generic_name")

    # Paginate results
    paginator = Paginator(generic_names, 100)
    page_number = request.GET.get("page")
    paginated_generic_names = paginator.get_page(page_number)

    # Offset for numbering
    offset = (paginated_generic_names.number - 1) * paginator.per_page

    view_context = {
        "generic_names": paginated_generic_names,
        "offset": offset,
    }

    context = TemplateLayout.init(request, view_context)

    return render(request, "add_genericName.html", context)



@login_required
def GenericAuditLogView(request):
    logs = GenericNameAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "generic_logs.html", context)



@login_required
def add_generic_name_view(request, pk=None):
    # Fetch the search query from the request
    search_query = request.GET.get("search_query", "").strip()

    # Fetch all generic names for the table
    generic_names = GenericName.objects.all().order_by("generic_name")  # Order by alphabetical order

    # Filter the queryset based on the search query
    if search_query:
        generic_names = generic_names.filter(
            Q(generic_name__icontains=search_query) |
            Q(brand_name__icontains=search_query)
        ).order_by("generic_name")  # Ensure filtered results are also ordered

    # Paginate the queryset
    paginator = Paginator(generic_names, 100)
    page_number = request.GET.get("page")
    paginated_generic_names = paginator.get_page(page_number)

    # Handle form submission for creating/editing generic names
    if pk:
        generic_name = get_object_or_404(GenericName, pk=pk)  # Fetch the specific generic name if editing
        form = GenericNameForm(request.POST or None, instance=generic_name)
        action = "update"  # Specify the action for logs
    else:
        generic_name = None  # Initialize generic_name to None for creation
        form = GenericNameForm(request.POST or None)
        action = "create"  # Specify the action for logs

    if request.method == "POST":
        if form.is_valid():
            generic_name = form.save(commit=False)  # Save the form data

            # Log the action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            # Set `created_by` only when creating a new generic name
            if action == "create" and worker:
                generic_name.created_by = worker

            generic_name.save()

            log_details = f"Generic Name {action}d by {'admin' if worker is None else worker}."
            GenericNameAuditLog.objects.create(
                user=worker,  # Worker who performed the action (or None if admin)
                generic_name=generic_name.generic_name,  # Log the generic name
                action=action,
                details=log_details
            )

            # Set success message and redirect
            messages.success(
                request, _("Generic Name {action}d successfully!".format(action=action))
            )
            return redirect('add-genericName')  # Redirect to generic name listing page

    # Prepare the context for the template
    view_context = {
        "form": form,
        "generic_name": generic_name,
        "generic_names": paginated_generic_names,  # Pass paginated generic names for the table
        "search_query": search_query,  # Pass the search query to the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)



@login_required
def edit_generic_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    generic_name = get_object_or_404(GenericName, pk=pk)
    generic_names = GenericName.objects.all()

    if request.method == "POST":
        # Populate the form with POST data and bind it to the instance
        form = GenericNameForm(request.POST, instance=generic_name)
        if form.is_valid():
            form.save()

            # Log the update action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            log_details = f"Generic Name '{generic_name.generic_name}' updated by {'admin' if worker is None else worker}."
            GenericNameAuditLog.objects.create(
                user=worker,
                generic_name=generic_name.generic_name,
                action="update",
                details=log_details
            )

            messages.success(request, _("Generic name updated successfully!"))
            return redirect('add-genericName')  # Redirect to the appropriate page
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        # Populate the form with existing data for GET requests
        form = GenericNameForm(instance=generic_name)

    view_context = {
        "form": form,
        "generic_names": generic_names,  # Pass the list of generic names to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_genericName.html', context)



@login_required
def delete_generic_view(request, pk):
    # Retrieve the GenericName instance or raise 404
    generic_name = get_object_or_404(GenericName, pk=pk)

    if request.method == "POST":
        # Log the delete action before deleting the instance
        try:
            worker = request.user.worker_profile  # Fetch worker profile
        except AttributeError:
            worker = None  # Handle case where no worker profile is linked

        log_details = f"Generic Name '{generic_name.generic_name}' deleted by {'admin' if worker is None else worker}."
        GenericNameAuditLog.objects.create(
            user=worker,
            generic_name=generic_name.generic_name,
            action="delete",
            details=log_details
        )

        # Delete the instance
        generic_name.delete()
        messages.success(request, _("Generic name deleted successfully!"))
        return redirect('add-genericName')  # Redirect to the appropriate page

    # Fetch all generic names for display (if needed)
    all_generic_names = GenericName.objects.all()

    view_context = {
        "genericName": all_generic_names,  # To display the list of generic names
        "item_to_delete": generic_name,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_genericName.html', context)
