from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.branches.models import Branch, BranchAuditLog

@receiver(post_save, sender=Branch)
def log_branch_save(sender, instance, created, **kwargs):
    from django.contrib.auth.models import User  # Import User to access request if needed
    user = None  # Replace with logic to get the current user, if possible

    action = "create" if created else "update"
    details = f"Branch {action.capitalize()}d: {instance.branch_name} (ID: {instance.id})"

    BranchAuditLog.objects.create(
        user=user,
        branch=instance,
        action=action,
        details=details
    )


@receiver(post_delete, sender=Branch)
def log_branch_delete(sender, instance, **kwargs):
    from django.contrib.auth.models import User  # Import User to access request if needed
    user = None  # Replace with logic to get the current user, if possible

    BranchAuditLog.objects.create(
        user=user,
        branch=instance,
        action="delete",
        details=f"Branch Deleted: {instance.branch_name} (ID: {instance.id})"
    )
