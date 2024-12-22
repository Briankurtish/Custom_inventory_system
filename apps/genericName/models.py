from django.db import models


class GenericName(models.Model):
    generic_name = models.CharField(
        max_length=255, unique=True, help_text="Generic Name"
    )
    brand_name = models.CharField(
        max_length=255, null=True, blank=True, help_text="Brand Name (optional)"
    )
    
    def __str__(self):
        return f"{self.generic_name} - {self.brand_name or 'No Brand'}"