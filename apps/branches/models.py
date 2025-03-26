from django.db import models
from django.contrib.auth.models import User


class Branch(models.Model):
    BRANCH_TYPES = [
        ("central", "Central Warehouse"),
        ("regular", "Regular Branch"),
    ]

    branch_id = models.CharField(
        max_length=50, unique=True
    )
    branch_name = models.CharField(
        max_length=255
    )
    address = models.TextField(

    )
    branch_type = models.CharField(
        max_length=10,
        choices=BRANCH_TYPES,
        default="regular",

    )

    branch_date_added = models.DateField(
        auto_now_add=True, null=True
    )

    created_by = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='branch_created'
    )



    def save(self, *args, **kwargs):
        if not self.branch_id:  # Only generate ID if not already set
            if self.branch_type == "regular":
                # Map branch names to their prefixes
                region_mapping = {
                    "Yaounde": "YDE",
                    "Douala": "DLA",
                    "Bafoussam": "BAF",
                    "Buea": "BUE",
                    "Tiko": "TIK",
                    "Limbe": "LIM",
                    "Dschang": "DSG",
                    "Edea": "EDA",
                    "Kumba": "KUM",
                    "Bamenda": "BDA",
                    "Bertoua": "BTA",
                    "Ngoundere": "NDG",
                    "Far North": "FNT",
                }

                # Get the region prefix from the branch name
                region_prefix = region_mapping.get(self.branch_name)
                if not region_prefix:
                    raise ValueError("Invalid Branch Name ... Not in range.")

                # Count existing branches with the same prefix
                existing_branches = Branch.objects.filter(
                    branch_id__startswith=f"{region_prefix}-"
                ).count()

                # Generate the branch ID
                self.branch_id = f"{region_prefix}-{existing_branches + 1:02d}"

            elif self.branch_type == "central":
                self.branch_id = "DLA-CWH"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch_id} - {self.branch_name} ({self.get_branch_type_display()})"



class BranchAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='log_created'
    )
    branch_name = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.branch_name} on {self.timestamp}"
