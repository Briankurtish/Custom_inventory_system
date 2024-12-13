from django.db import models


class GenericName(models.Model):
    generic_name = models.CharField(
        max_length=255, unique=True, help_text="Generic Name"
    )
    
    def __str__(self):
        return f"{self.generic_name}"