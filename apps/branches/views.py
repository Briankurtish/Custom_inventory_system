from django.views.generic import TemplateView
from apps.workers.models import Worker
from web_project import TemplateLayout
from django.shortcuts import get_object_or_404, render, redirect
from .models import Branch, BranchAuditLog
from .forms import BranchForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _





"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


@login_required
def ManageBranchView(request):
    branch = Branch.objects.all()
    paginator = Paginator(branch, 10)
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_branch = paginator.get_page(page_number)  # Get the page object

    # Create a new context dictionary for this view
    view_context = {
        "branch": paginated_branch,
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'branches.html', context)


@login_required
def BranchAuditLogView(request):
    logs = BranchAuditLog.objects.all().order_by('-timestamp')
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

    return render(request, "branch_logs.html", context)


@login_required
def add_branch_view(request, pk=None):
    if pk:
        branch = get_object_or_404(Branch, pk=pk)
        form = BranchForm(request.POST or None, instance=branch)
        action = "update"  # Specify the action for logs
    else:
        branch = None  # Initialize branch to None
        form = BranchForm(request.POST or None)
        action = "create"  # Specify the action for logs

    # Handle the POST request (form submission)
    if request.method == "POST":
        if form.is_valid():
            branch = form.save()  # Save the form and set the branch variable

            # Capture the branch details before saving
            branch_details = {
                "id": branch.id,
                "name": branch.branch_name,
            }

            # Handle the audit log
            if request.user.username == "admin":
                # Special case for admin account (no associated Worker)
                BranchAuditLog.objects.create(
                    user=None,  # No associated Worker
                    branch_name=branch_details["name"],  # Store branch name directly
                    action=action,
                    details=f"Branch {action}d by admin."
                )
            else:
                # Try to retrieve the Worker instance
                try:
                    worker = request.user.worker_profile
                    BranchAuditLog.objects.create(
                        user=worker,
                        branch_name=branch_details["name"],  # Store branch name directly
                        action=action,
                        details=f"Branch {action}d by {worker}."
                    )
                except Worker.DoesNotExist:
                    messages.error(request, "Worker profile not found for the current user.")
                    return redirect("branches")  # Handle error appropriately

            messages.success(request, _("Branch Created Successfully" if action == "create" else "Branch Updated Successfully"))
            return redirect('branches')  # Redirect to the branch list after saving

    view_context = {
        "form": form,
        "is_editing": bool(pk),  # Flag to indicate if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addBranch.html', context)


@login_required
def update_branch_view(request, pk):
    branch = get_object_or_404(Branch, pk=pk)

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            branch = form.save()

            # Capture the branch details before saving
            branch_details = {
                "id": branch.id,
                "name": branch.branch_name,
            }

            # Handle the audit log
            if request.user.username == "admin":
                # Special case for admin account (no associated Worker)
                BranchAuditLog.objects.create(
                    user=None,  # No associated Worker
                    branch_name=branch_details["name"],  # Store branch name directly
                    action="update",
                    details=f"Branch updated by admin."
                )
            else:
                # Try to retrieve the Worker instance
                try:
                    worker = request.user.worker_profile
                    BranchAuditLog.objects.create(
                        user=worker,
                        branch_name=branch_details["name"],  # Store branch name directly
                        action="update",
                        details=f"Branch updated by {worker}."
                    )
                except Worker.DoesNotExist:
                    messages.error(request, "Worker profile not found for the current user.")
                    return redirect("branches")  # Handle error appropriately

            messages.success(request, _("Branch Updated Successfully"))
            return redirect("branches")
    else:
        form = BranchForm(instance=branch)

    branches = Branch.objects.all()

    view_context = {
        "form": form,
        "branches": branches,
        "is_editing": True,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addBranch.html', context)



@login_required
def delete_branch_view(request, pk):
    """
    Handles saving the delete log for a branch and then deleting the branch.
    """
    branch = get_object_or_404(Branch, id=pk)

    if request.method == "POST":
        # Capture branch details before deletion
        branch_details = {
            "id": branch.id,
            "name": branch.branch_name,
        }

        # Handle the audit log before deletion
        if request.user.username == "admin":
            # Special case for admin account (no associated Worker)
            BranchAuditLog.objects.create(
                user=None,  # No associated Worker
                branch_name=branch_details["name"],  # Store branch name directly
                action="delete",
                details=f"Branch '{branch_details['name']}' deleted by admin."
            )
        else:
            # Try to retrieve the Worker instance
            try:
                worker = request.user.worker_profile
                BranchAuditLog.objects.create(
                    user=worker,
                    branch_name=branch_details["name"],  # Store branch name directly
                    action="delete",
                    details=f"Branch '{branch_details['name']}' deleted by {worker}."
                )
            except Worker.DoesNotExist:
                messages.error(request, "Worker profile not found for the current user.")
                return redirect("branches")  # Handle error appropriately

        # Now, delete the branch
        branch.delete()

        messages.success(request, _("Branch Deleted Successfully"))
        return redirect("branches")

    view_context = {
        "branch": branch,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteBranch.html', context)
