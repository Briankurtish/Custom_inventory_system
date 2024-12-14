from django.db import models


class PackSize(models.Model):
    pack_size = models.CharField(
        max_length=255, unique=True, help_text="Pack Size"
    )
    
    def __str__(self):
        return f"{self.pack_size}"