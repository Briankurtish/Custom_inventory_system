from django.db import models

class Batch(models.Model):
    batch_number = models.CharField(
        max_length=50, unique=True, help_text="Numéro de lot"
    )
    expiry_date = models.DateField(help_text="Date d’expiration")

    def __str__(self):
        return f"Batch {self.batch_number} - Expiry: {self.expiry_date}"


class Product(models.Model):
    product_code = models.CharField(
        max_length=50, unique=True, blank=True, help_text="Code produit"
    )
    brand_name = models.CharField(
        max_length=255, help_text="Designation"
    )
    generic_name_dosage = models.CharField(
        max_length=255, help_text="DCI et Dosage"
    )
    pack_size = models.CharField(
        max_length=100, help_text="Conditionnement"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Unit Price of the product"
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="products", help_text="Batch associated with this product"
    )

    class Meta:
        unique_together = ("product_code", "batch")

    def __str__(self):
        return f"{self.product_code} - {self.brand_name} ({self.generic_name_dosage}) - Batch {self.batch.batch_number}"

    def save(self, *args, **kwargs):
        if not self.product_code:
            last_product = Product.objects.order_by('id').last()
            if last_product and last_product.product_code.startswith("GCP"):
                last_number = int(last_product.product_code[3:])  # Extract the number part
                self.product_code = f"GCP{last_number + 1:04d}"  # Increment and pad with zeros
            else:
                self.product_code = "GCP0001"  # Start from GCP0001
        super().save(*args, **kwargs)