# web_project/context_processors.py
from django.db.models import Sum
from apps.orders.models import Invoice
from apps.orders.models import PurchaseOrder
from apps.stock_request.models import StockRequest
from apps.workers.models import Worker, RolePrivilege  # Import the Worker model

def pending_counts(request):
    """
    A context processor to add counts of pending deposits, withdrawals, and online users to all templates.
    """
    if request.user.is_authenticated:
        # Fetch real-time counts directly from the database
        unpaid_invoices_count = Invoice.objects.filter(status='Unpaid').count()
        pending_orders_count = PurchaseOrder.objects.filter(status='Pending').count()
        pending_request_count = StockRequest.objects.filter(status='Pending').count()

        # Count the number of online users
        online_users_count = Worker.objects.filter(is_online=True).count()

        return {
            "unpaid_invoices_count": unpaid_invoices_count,
            'pending_orders_count': pending_orders_count,
            'pending_request_count': pending_request_count,
            'online_users_count': online_users_count,  # Add online users count
        }
    return {}

def role_privileges(request):
    """
    A context processor to add role-based privileges to the template context.
    """
    context = {}
    if request.user.is_authenticated:
        if hasattr(request.user, 'worker_profile'):
            role = request.user.worker_profile.role
            try:
                role_privilege = RolePrivilege.objects.filter(role=role).first()
                if role_privilege:
                    # Combine both role privileges and worker-specific privileges
                    privileges = set(role_privilege.privileges.all()) | set(request.user.worker_profile.privileges.all())
                    context['role_privileges'] = list(privileges)
                else:
                    context['role_privileges'] = []
            except RolePrivilege.DoesNotExist:
                context['role_privileges'] = []
        else:
            context['role_privileges'] = []
    return context
