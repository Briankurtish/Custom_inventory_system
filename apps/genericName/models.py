from django.db import models

from apps.workers.models import Worker


class GenericName(models.Model):
    generic_name = models.CharField(
        max_length=255, unique=True
    )
    brand_name = models.CharField(
        max_length=255, null=True, blank=True
    )

    old_brand_name = models.CharField(
        max_length=255, null=True, blank=True
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='genericname_created'
    )

    def __str__(self):
        return f"{self.generic_name}"


class GenericNameAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='generic_log_created'
    )
    generic_name = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.generic_name} on {self.timestamp}"
