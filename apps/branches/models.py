from django.db import models

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

    def save(self, *args, **kwargs):
        if not self.branch_id:  # Only generate ID if not already set
            if self.branch_type == "regular":
                # Map branch names to their prefixes
                region_mapping = {
                    "Yaounde Branch": "YDE",
                    "Douala Branch": "DLA",
                    "Bafoussam Branch": "BAF"
                }

                # Get the region prefix from the branch name
                region_prefix = region_mapping.get(self.branch_name)
                if not region_prefix:
                    raise ValueError("Branch name must be 'Yaounde', 'Douala', or 'Bafoussam' for regular branches.")

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
