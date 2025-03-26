from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.customers.models import Customer, CustomerAuditLog

@receiver(post_save, sender=Customer)
def log_customer_save(sender, instance, created, **kwargs):
    from django.contrib.auth.models import User  # Import User to access request if needed
    user = None  # Replace with logic to get the current user, if possible

    action = "create" if created else "update"
    details = f"Customer {action.capitalize()}d: {instance.customer_name} (ID: {instance.id})"

    CustomerAuditLog.objects.create(
        user=user,
        customer_name=instance,
        action=action,
        details=details
    )


@receiver(post_delete, sender=Customer)
def log_customer_delete(sender, instance, **kwargs):
    from django.contrib.auth.models import User  # Import User to access request if needed
    user = None  # Replace with logic to get the current user, if possible

    CustomerAuditLog.objects.create(
        user=user,
        customer_name=instance,
        action="delete",
        details=f"Customer Deleted: {instance.customer_name} (ID: {instance.id})"
    )
