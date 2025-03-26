from django.db import models

from apps.workers.models import Worker


class PackSize(models.Model):
    pack_size = models.CharField(
        max_length=255, unique=True
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='packsize_created'
    )

    def __str__(self):
        return f"{self.pack_size}"


class PackSizeAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pack_log_created'
    )
    pack_size = models.CharField(max_length=255, null=True, blank=True)  # Log the pack size
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.pack_size} on {self.timestamp}"
