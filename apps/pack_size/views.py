from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import PackSize, PackSizeAuditLog
from .forms import PackSizeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator

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


@login_required
def PackSizeAuditLogView(request):
    logs = PackSizeAuditLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 100)  # Paginate logs with 100 logs per page
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

    return render(request, "packsize_logs.html", context)



@login_required
def add_pack_view(request):
    pack_size = PackSize.objects.all()

    if request.method == "POST":
        form = PackSizeForm(request.POST)
        if form.is_valid():
            pack_size = form.save(commit=False)  # Save the form data

            # Log the create action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            if worker:
                pack_size.created_by = worker

            pack_size.save()

            log_details = f"Pack Size '{pack_size.pack_size}' created by {'admin' if worker is None else worker}."
            PackSizeAuditLog.objects.create(
                user=worker,
                pack_size=pack_size.pack_size,  # Log the pack size
                action="create",
                details=log_details
            )

            messages.success(request, _("Pack Size added successfully!"))
            return redirect('add-packsize')
    else:
        form = PackSizeForm()

    view_context = {
        "form": form,
        "pack_size": pack_size,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_packsize.html', context)


# @login_required
# def add_pack_view(request):
#     pack_sizes = PackSize.objects.all()

#     if request.method == "POST":
#         form = PackSizeForm(request.POST)
#         if form.is_valid():
#             pack_size = form.save(commit=False)  # Save without committing to DB

#             try:
#                 worker = request.user.worker_profile  # Fetch worker profile
#             except AttributeError:
#                 worker = None  # Handle case where no worker profile is linked

#             # Set `created_by` only if a worker is available
#             if worker:
#                 pack_size.created_by = worker

#             pack_size.save()  # Now save to DB

#             # Log the create action
#             log_details = f"Pack Size '{pack_size.pack_size}' created by {'admin' if worker is None else worker}."
#             PackSizeAuditLog.objects.create(
#                 user=worker,
#                 pack_size=pack_size.pack_size,  # Log the pack size
#                 action="create",
#                 details=log_details
#             )

#             messages.success(request, _("Pack Size added successfully!"))
#             return redirect('add-packsize')
#     else:
#         form = PackSizeForm()

#     view_context = {
#         "form": form,
#         "pack_sizes": pack_sizes,
#     }
#     context = TemplateLayout.init(request, view_context)

#     return render(request, 'add_packsize.html', context)



@login_required
def edit_pack_view(request, pk):
    pack_size_instance = get_object_or_404(PackSize, pk=pk)  # Get the specific pack size
    pack_size_list = PackSize.objects.all()  # Fetch all pack sizes for the table

    if request.method == "POST":
        form = PackSizeForm(request.POST, instance=pack_size_instance)
        if form.is_valid():
            form.save()

            # Log the update action
            try:
                worker = request.user.worker_profile  # Fetch worker profile
            except AttributeError:
                worker = None  # Handle case where no worker profile is linked

            log_details = f"Pack Size '{pack_size_instance.pack_size}' updated by {'admin' if worker is None else worker}."
            PackSizeAuditLog.objects.create(
                user=worker,
                pack_size=pack_size_instance.pack_size,  # Log the pack size
                action="update",
                details=log_details
            )

            messages.success(request, _("Pack Size updated successfully!"))
            return redirect('add-packsize')
    else:
        form = PackSizeForm(instance=pack_size_instance)

    view_context = {
        "form": form,
        "pack_size": pack_size_list,  # Pass the list of pack sizes to the template
        "is_editing": True,  # Flag to indicate editing mode in the template
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'add_packsize.html', context)



@login_required
def delete_pack_view(request, pk):
    pack_size = get_object_or_404(PackSize, pk=pk)  # Get the pack size by ID

    if request.method == "POST":
        # Log the delete action before deleting the instance
        try:
            worker = request.user.worker_profile  # Fetch worker profile
        except AttributeError:
            worker = None  # Handle case where no worker profile is linked

        log_details = f"Pack Size '{pack_size.pack_size}' deleted by {'admin' if worker is None else worker}."
        PackSizeAuditLog.objects.create(
            user=worker,
            pack_size=pack_size.pack_size,  # Log the pack size
            action="delete",
            details=log_details
        )

        # Delete the instance
        pack_size.delete()
        messages.success(request, _("Pack Size deleted successfully!"))
        return redirect('add-packsize')  # Redirect to the pack size list

    pack_size_list = PackSize.objects.all()  # Fetch all pack sizes for display

    view_context = {
        "pack_size": pack_size_list,  # To display the list of pack sizes
        "item_to_delete": pack_size,  # Pass the item to delete for confirmation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'delete_packsize.html', context)
