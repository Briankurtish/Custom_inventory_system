from django.db import models

# Create your models here.
class Branch(models.Model):
    BRANCH_TYPES = [
        ("central", "Central Warehouse"),
        ("regular", "Regular Branch"),
    ]

    branch_id = models.CharField(
        max_length=50, unique=True, help_text="Branch Identifier"
    )
    branch_name = models.CharField(
        max_length=255, help_text="Branch Name"
    )
    address = models.TextField(
        help_text="Branch Address"
    )
    branch_type = models.CharField(
        max_length=10,
        choices=BRANCH_TYPES,
        default="regular",
        help_text="Type of branch (Central or Regular)"
    )

    def __str__(self):
        return f"{self.branch_id} - {self.branch_name} ({self.get_branch_type_display()})"
