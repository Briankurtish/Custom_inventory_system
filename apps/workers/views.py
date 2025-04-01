from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.generic import TemplateView
from apps.branches.models import Branch
from web_project import TemplateLayout
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from .models import EmployeeIDCounter, Privilege, RolePrivilege, Worker
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RolePrivilegeForm, SecurityPinForm, UserCreationForm, WorkerForm, WorkerPrivilegeForm, PrivilegeForm, WorkerProfileForm
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import authenticate
import json
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.db.models import Prefetch
from collections import defaultdict


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""

@login_required
def ManageWorkerView(request):
    search_query = request.GET.get("search_query", "").strip()
    role_filter = request.GET.get("role", "")
    branch_filter = request.GET.get("branch", "")
    department_filter = request.GET.get("department", "")
    company_filter = request.GET.get("company", "")
    status_filter = request.GET.get("status", "")

    # Fetch all workers ordered by employee ID
    workers = Worker.objects.all().order_by("employee_id")

    # Apply filters
    if search_query:
        workers = workers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )

    if role_filter:
        workers = workers.filter(role=role_filter)

    if branch_filter:
        workers = workers.filter(branch__id=branch_filter)

    if department_filter:
        workers = workers.filter(department=department_filter)

    if company_filter:
        workers = workers.filter(company=company_filter)

    if status_filter == "active":
        workers = workers.filter(is_active=True)
    elif status_filter == "inactive":
        workers = workers.filter(is_active=False)

    # Fetch choices for dropdowns
    branches = Branch.objects.all()
    roles = Worker.ROLE_CHOICES
    departments = Worker.DEPARTMENT_CHOICES
    companies = Worker.COMPANY

    # Paginate workers (100 per page)
    paginator = Paginator(workers, 100)
    page_number = request.GET.get("page")
    paginated_workers = paginator.get_page(page_number)

    offset = (paginated_workers.number - 1) * paginator.per_page

    # Context for template
    view_context = {
        "workers": paginated_workers,
        "branches": branches,
        "roles": roles,
        "departments": departments,
        "companies": companies,
        "offset": offset,
        "search_query": search_query,
        "role_filter": role_filter,
        "branch_filter": branch_filter,
        "department_filter": department_filter,
        "company_filter": company_filter,
        "status_filter": status_filter,
    }

    context = TemplateLayout.init(request, view_context)
    return render(request, "workers.html", context)



@login_required
def assign_privileges_to_role(request):
    roles = [role[0] for role in Worker.ROLE_CHOICES]
    role = request.GET.get('role')  # Get selected role from query parameters
    role_privilege = None  

    privileges_by_category = defaultdict(list)
    all_privileges = Privilege.objects.all()

    for privilege in all_privileges:
        privileges_by_category[privilege.category].append(privilege)

    if request.method == 'POST':
        role = request.POST.get('role')
        try:
            role_privilege = RolePrivilege.objects.get(role=role)
            form = RolePrivilegeForm(request.POST, instance=role_privilege)
        except RolePrivilege.DoesNotExist:
            form = RolePrivilegeForm(request.POST)

        if form.is_valid():
            role_privilege = form.save(commit=False)
            role_privilege.role = role  
            role_privilege.save()
            form.save_m2m()
            messages.success(request, _('Privileges updated successfully!'))
            return redirect('workers')  

    else:
        if role:
            try:
                role_privilege = RolePrivilege.objects.get(role=role)
                form = RolePrivilegeForm(instance=role_privilege)
            except RolePrivilege.DoesNotExist:
                form = RolePrivilegeForm(initial={'role': role})
        else:
            form = RolePrivilegeForm()

    context = TemplateLayout.init(request, {
        'form': form,
        'roles': roles,
        'privileges_by_category': dict(privileges_by_category),
    })
    return render(request, 'assign_privileges.html', context)



@login_required
def change_worker_role(request, worker_id):
    worker = get_object_or_404(Worker, pk=worker_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        
        if new_role and new_role != worker.role:
            try:
                role_privilege = RolePrivilege.objects.get(role=new_role)
                worker.role = new_role
                worker.privileges.set(role_privilege.privileges.all())
                worker.save()
                messages.success(request, "Role updated successfully!")
            except RolePrivilege.DoesNotExist:
                worker.role = new_role
                worker.privileges.clear()
                worker.save()
                messages.success(request, "Role updated (no privileges for this role)")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('worker_detail', worker_id=worker.id)
    
    # Get all roles directly from the model
    roles = Worker.ROLE_CHOICES
    
    return JsonResponse({
        'success': False,
        'roles': roles,
        'current_role': worker.role
    }, status=400)



@login_required
def OnlineWorkersView(request):
    """
    View to get all online workers.
    """
    online_workers = Worker.objects.filter(is_online=True).order_by('employee_id')

    # Paginate workers: Show 10 workers per page
    paginator = Paginator(online_workers, 100)
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_workers = paginator.get_page(page_number)  # Get the page object

    offset = (paginated_workers.number - 1) * paginator.per_page

    # Create a new context dictionary for this view
    view_context = {
        "workers": paginated_workers,  # Pass the paginated workers to the template
        "offset": offset,  # Pass the offset to the template
    }

    # Initialize the template layout and merge the view context
    context = TemplateLayout.init(request, view_context)

    return render(request, 'online_workers.html', context)

@login_required
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
            messages.success(request, _('Employee Credentials created successfully!'))
            return redirect('workers')  # Redirect to the product list after saving

    view_context = {
        "form": form,
        "is_editing": bool(pk),  # Flag to indicate if we are editing
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addWorker.html', context)


@login_required
def toggle_worker_status(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.is_active = not worker.is_active
    worker.save()
    if worker.is_active:
        messages.success(request, _("Worker has been activated."))
    else:
        messages.success(request, _("Worker has been deactivated."))
    return redirect('workers')  # Redirect to worker list



def change_worker_password(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in after password change
            messages.success(request, "Password successfully updated!")
            return redirect('workers')  # Redirect to the worker list
    else:
        form = PasswordChangeForm(user)

    view_context = {'form': form, 'worker': user.worker_profile}
    context = TemplateLayout.init(request, view_context)

    return render(request, 'change_password.html', context)


@login_required
def delete_worker_view(request, pk):
    """
    Delete a worker and their associated user account, and adjust the counter.
    """
    worker = get_object_or_404(Worker, pk=pk)  # Fetch the worker to delete

    # Determine the prefix based on the worker's employee ID
    employee_id_parts = worker.employee_id.split('-')
    prefix = '-'.join(employee_id_parts[:-1]) if len(employee_id_parts) > 1 else None

    # Assuming the Worker model has a foreign key or one-to-one relationship with User
    associated_user = worker.user if hasattr(worker, 'user') else None

    if request.method == "POST":
        # Delete the associated user if it exists
        if associated_user:
            associated_user.delete()

        # Decrement the counter if a valid prefix exists
        if prefix:
            EmployeeIDCounter.decrement(prefix)

        # Delete the worker
        worker.delete()

        messages.success(request, _('Worker and associated user deleted successfully!'))
        return redirect('workers')  # Redirect to the workers list after deletion

    # Render a confirmation page
    view_context = {
        "worker": worker,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'deleteWorker.html', context)



@login_required
def update_worker_view(request, pk):
    worker = get_object_or_404(Worker, pk=pk)  # Get the product by ID

    if request.method == "POST":
        form = WorkerForm(request.POST, instance=worker)  # Bind form to the product instance
        if form.is_valid():
            form.save()
            messages.success(request, _('Employee Credentials updated successfully!'))
            return redirect('workers')  # Redirect to the product list
    else:
        form = WorkerForm(instance=worker)

    view_context = {
        "form": form,
        "is_editing": True,  # Flag for edit operation
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'addWorker.html', context)



@login_required
def edit_worker_profile_view(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, request.FILES, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, _("Worker profile updated successfully!"))
            return redirect('edit_worker_profile', pk=worker.pk)  # Redirect to worker detail or list
    else:
        form = WorkerProfileForm(instance=worker, initial={
            'first_name': worker.user.first_name,
            'last_name': worker.user.last_name,
        })

    view_context = {'form': form, 'worker': worker}
    context = TemplateLayout.init(request, view_context)

    return render(request, 'updateProfile.html', context)


@login_required
def password_change_view(request):
    """
    View for users to change their password.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Keep the user logged in after password change
            messages.success(request, 'Your password was successfully updated!')
            return redirect('index')  # Redirect to a success page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)

    view_context = {'form': form}
    context = TemplateLayout.init(request, view_context)

    return render(request, 'change_password.html', context)




@login_required
def manage_worker_privileges(request, worker_id):
    """
    View for managing privileges of a specific worker.
    - Role-based privileges are pre-checked (cannot be removed).
    - Extra privileges can be added to the worker.
    """
    worker = get_object_or_404(Worker, id=worker_id)

    # Get worker's role
    worker_role = worker.role

    # Fetch role-based privileges (privileges assigned to the worker's role)
    try:
        role_privilege = RolePrivilege.objects.get(role=worker_role)
        role_privileges = role_privilege.privileges.all()
    except RolePrivilege.DoesNotExist:
        role_privileges = Privilege.objects.none()

    # Fetch privileges directly assigned to this worker
    worker_privileges = worker.privileges.all()

    # All privileges (for checkbox listing)
    all_privileges = Privilege.objects.all()

    if request.method == 'POST':
        selected_privilege_ids = request.POST.getlist('privileges')  # Get selected privileges

        # Convert to actual Privilege objects
        selected_privileges = Privilege.objects.filter(id__in=selected_privilege_ids)

        # Worker should always have role-based privileges
        worker.privileges.set(role_privileges | selected_privileges)  # Union of both sets

        messages.success(request, _('Employee Privileges updated successfully!'))
        return redirect('workers')  # Redirect to workers page

    view_context = {
        "worker": worker,
        "all_privileges": all_privileges,
        "role_privileges": role_privileges,
        "worker_privileges": worker_privileges,
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'manage_privileges.html', context)



@login_required
def create_privilege(request):
    """
    View to allow the admin to create a new privilege and list existing privileges.
    """
    privileges = Privilege.objects.all().order_by("name")  # Fetch all privileges

    if request.method == "POST":
        form = PrivilegeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Privilege created successfully!"))
            return redirect("create_privilege")
        else:
            messages.error(request, _("Error creating privilege. Please check the input."))
    else:
        form = PrivilegeForm()

    view_context = {
        "form": form,
        "privileges": privileges,  # Pass privileges to the template
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "create_privilege.html", context)


@login_required
def edit_privilege(request, privilege_id):
    """
    View to edit an existing privilege.
    """
    privilege = get_object_or_404(Privilege, id=privilege_id)
    privileges = Privilege.objects.all().order_by("name")

    if request.method == "POST":
        form = PrivilegeForm(request.POST, instance=privilege)
        if form.is_valid():
            form.save()
            messages.success(request, _("Privilege updated successfully!"))
            return redirect("create_privilege")  # Redirect back to the privilege list
        else:
            messages.error(request, _("Error updating privilege. Please check the input."))
    else:
        form = PrivilegeForm(instance=privilege)

    view_context = {
        "form": form,
        "privilege": privilege,
        "privileges": privileges,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, "create_privilege.html", context)


@login_required
def get_roles_and_privileges(request):
    """
    View to fetch all roles and their default privileges with descriptions.
    """
    # Extract roles from Worker.ROLE_CHOICES
    roles = [role[0] for role in Worker.ROLE_CHOICES]

    # Handle GET request
    if request.method == 'GET':
        selected_role = request.GET.get('role', None)  # Role selected by user

        # Fetch privileges for the selected role from the database
        privileges = []
        if selected_role:
            try:
                role_privilege = RolePrivilege.objects.get(role=selected_role)
                privileges = role_privilege.privileges.all().values('name', 'description')
            except RolePrivilege.DoesNotExist:
                # If no privileges are assigned to the role, return an empty list
                privileges = []

        view_context = {
            'roles': roles,
            'privileges': list(privileges),  # Convert QuerySet to list
            'selected_role': selected_role,
        }

        context = TemplateLayout.init(request, view_context)
        return render(request, 'privilege_details.html', context)

    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required
def create_security_pin(request):
    """
    View to create a security PIN for the worker.
    """
    worker = request.user.worker_profile

    if request.method == 'POST':
        form = SecurityPinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            worker.set_security_pin(pin)
            worker.save()
            messages.success(request, "Security PIN created successfully!")
            return redirect('index')
    else:
        form = SecurityPinForm()

    view_context = {'form': form, 'worker':worker}

    context = TemplateLayout.init(request, view_context)

    return render(request, 'security_pin.html', context)

@login_required
def update_security_pin(request):
    """
    View to update the security PIN for the worker.
    """
    worker = request.user.worker_profile

    if request.method == 'POST':
        form = SecurityPinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            worker.set_security_pin(pin)
            worker.save()
            messages.success(request, "Security PIN updated successfully!")
            return redirect('index')
    else:
        form = SecurityPinForm()

    view_context = {'form': form, 'worker':worker}

    context = TemplateLayout.init(request, view_context)

    return render(request, 'security_pin.html', context)



@login_required
def validate_password(request):
    """
    Validate the user's password via AJAX.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON request
            password = data.get('password')
        except json.JSONDecodeError:
            return JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)

        if request.user.check_password(password):  # Validate password properly
            return JsonResponse({'valid': True})
        else:
            return JsonResponse({'valid': False, 'error': 'Incorrect password'})

    return JsonResponse({'valid': False, 'error': 'Invalid request method'}, status=405)


@login_required
def validate_security_pin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            entered_pin = data.get("pin")
        except json.JSONDecodeError:
            return JsonResponse({"valid": False, "error": "Invalid JSON"}, status=400)

        # Ensure the PIN is provided
        if not entered_pin or len(entered_pin) != 4 or not entered_pin.isdigit():
            return JsonResponse({"valid": False, "error": "Invalid PIN format"}, status=400)

        user_profile = request.user.worker_profile

        # Check if the security PIN exists and validate it
        if user_profile.security_pin and check_password(entered_pin, user_profile.security_pin):
            return JsonResponse({"valid": True})
        else:
            return JsonResponse({"valid": False, "error": "Incorrect PIN"}, status=400)

    return JsonResponse({"valid": False, "error": "Invalid request method"}, status=405)


@login_required
def check_security_pin(request):
    """
    API view to check if the user has a security PIN.
    """
    user_profile = request.user.worker_profile
    has_pin = bool(user_profile.security_pin)  # Check if PIN exists

    return JsonResponse({"has_pin": has_pin})
