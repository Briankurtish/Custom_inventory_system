from django.http import JsonResponse
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from .models import Worker
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserCreationForm, WorkerForm, WorkerPrivilegeForm, PrivilegeForm


"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to tables/urls.py file for more pages.
"""


def ManageWorkerView(request):
    workers = Worker.objects.all()
    
    # Paginate workers: Show 10 workers per page
    paginator = Paginator(workers, 5) 
    page_number = request.GET.get('page')  # Get the current page number from the request
    paginated_workers = paginator.get_page(page_number)  # Get the page object
    
    # Create a new context dictionary for this view
    view_context = {
        "workers": paginated_workers,  # Pass the paginated workers to the template
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



@login_required
def manage_worker_privileges(request, worker_id):
    """
    View for adding/removing privileges from a specific worker.
    """
    worker = get_object_or_404(Worker, id=worker_id)

    if request.method == 'POST':
        form = WorkerPrivilegeForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            return redirect('workers')  # Redirect to a list of workers or success page
    else:
        form = WorkerPrivilegeForm(instance=worker)
        
        view_context = {
        "form": form,
        "worker": worker,  
    }
    context = TemplateLayout.init(request, view_context)

    return render(request, 'manage_privileges.html', context)


def create_privilege(request):
    """
    View to allow the admin to create a new privilege.
    """
    if request.method == 'POST':
        form = PrivilegeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Privilege created successfully!')
            return redirect('create_privilege')
        else:
            messages.error(request, 'Error creating privilege. Please check the input.')
    else:
        form = PrivilegeForm()

    view_context = {
        "form": form,
    }
    context = TemplateLayout.init(request, view_context)
    return render(request, 'create_privilege.html', context)

def get_roles_and_privileges(request):
    """
    View to fetch all roles and their default privileges.
    """
    roles = [role[0] for role in Worker.ROLE_CHOICES]  # Extract roles from ROLE_CHOICES

    if request.method == 'GET':
        selected_role = request.GET.get('role', None)  # Role selected by the user
        privileges = []

        if selected_role:
            # Fetch default privileges based on the selected role
            default_privileges = {
                'Director': ['Manage Users', 'View Reports', 'Manage Inventory'],
                'Marketing Director': ['View Stocks', 'Request Stock'],
                'Pharmacist': ['Recommend Medical Products', 'Prepare Customs Clearing Report', 'Creates Good Receipt Note', 'Accept or Decline Stock Requisition'],
                'Accountant': ['View Reports', 'Manage Finances'],
                'Central Stock Manager': ['Manage Inventory', 'View Stocks', "View Products", "View Approved Requests", 'Transfer Stock'],
                'Stock Manager': ['Manage Inventory', 'View Stocks'],
                'Cashier': ['Process Payments'],
                'Sales Rep': ['View Orders', 'Create Orders'],
            }
            privileges = default_privileges.get(selected_role, [])

        view_context = {
            'roles': roles,
            'privileges': privileges,
            'selected_role': selected_role,
        }

        context = TemplateLayout.init(request, view_context)
        return render(request, 'privilege_details.html', context)

    return JsonResponse({'error': 'Invalid request'}, status=400)
