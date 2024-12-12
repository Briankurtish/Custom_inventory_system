from django.db import models

# Create your models here.
class Branch(models.Model):
    branch_id = models.CharField(
        max_length=50, unique=True, help_text="Branch Identifier"
    )
    branch_name = models.CharField(
        max_length=255, help_text="Branch Name"
    )
    address = models.TextField(
        help_text="Branch Address"
    )

    def __str__(self):
        return f"{self.branch_id} - {self.branch_name}"
