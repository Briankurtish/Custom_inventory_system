from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Worker, Privilege

@receiver(post_save, sender=Worker)
def assign_default_privileges(sender, instance, created, **kwargs):
    """
    Signal to assign default privileges to a worker after creation.
    """
    if created:  # Only when a new Worker is created
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

        role_privileges = default_privileges.get(instance.role, [])
        for privilege_name in role_privileges:
            privilege, _ = Privilege.objects.get_or_create(name=privilege_name)
            instance.privileges.add(privilege)
