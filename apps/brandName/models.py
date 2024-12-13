from django.db import models

class BrandName(models.Model):
    brand_name = models.CharField(
        max_length=255, unique=True, help_text="Brand Name"
    )
    
    def __str__(self):
        return f"{self.brand_name}"


class BrandNameModel(models.Model):
    brand_name = models.CharField(
        max_length=255, unique=True, help_text="Brand Name"
    )
    
    def __str__(self):
        return f"{self.brand_name}"