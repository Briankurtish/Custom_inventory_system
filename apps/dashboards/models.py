from django.db import models
from django.utils import timezone
from apps.workers.models import Worker



class Notice(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name="notice_created_by"
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']  # Newest notices first

    def __str__(self):
        return self.title
