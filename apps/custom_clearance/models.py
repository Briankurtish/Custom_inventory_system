from django.db import models
from django.contrib.auth.models import User

class ClearanceProcessGroup(models.Model):
    """Represents a clearance process session per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bol_number = models.CharField(
        max_length=255, null=True
    )
    bol_document = models.FileField(null=True,upload_to="clearance_documents/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Clearance Process {self.id} for {self.user.username}"

class ClearanceStep(models.Model):
    """Represents each step in the clearance process."""
    step_number = models.FloatField(unique=True)
    name = models.CharField(max_length=255)
    required_document = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ClearanceProcess(models.Model):
    """Tracks completion of a step within a specific clearance session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    process_group = models.ForeignKey(ClearanceProcessGroup, on_delete=models.CASCADE, related_name="steps", null=True)
    step = models.ForeignKey(ClearanceStep, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    document = models.FileField(upload_to="clearance_documents/")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.step.name} - {self.user.username}"


class CustomLogs(models.Model):
    ACTION_CHOICES = [
        ('SESSION_START', 'Started New Clearance Session'),
        ('STEP_COMPLETED', 'Completed Clearance Step'),
        ('STEP_ADDED', 'Added a New Step'),
        ('REDIRECTED', 'Redirected to Start New Session'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
