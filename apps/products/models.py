from django.db import models
from django.db import IntegrityError
from apps.genericName.models import GenericName


class Batch(models.Model):
    batch_number = models.CharField(
        max_length=50, unique=True, help_text="Batch Number"
    )
    generic_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name='batches', help_text="Generic Name"
    )
    expiry_date = models.DateField(help_text="Expiry Date")
    
    def __str__(self):
        return f"Batch: {self.batch_number} -- {self.generic_name.generic_name} - Expiry: {self.expiry_date}"



class Product(models.Model):
    product_code = models.CharField(
        max_length=50, blank=True, help_text="Code produit"
    )
    brand_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="brand_products", help_text="Brand Name associated with this product"
    )
    generic_name_dosage = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="dosage_products", help_text="Generic Name associated with this product", null=True, blank=True
    )
    pack_size = models.ForeignKey(
        "pack_size.PackSize", on_delete=models.CASCADE, related_name="products", help_text="Pack Size associated with this product"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Unit Price of the product"
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="products", help_text="Batch associated with this product"
    )

    class Meta:
        unique_together = ("brand_name", "batch")  # Ensure each brand_name and batch combination is unique

    def __str__(self):
        return f"{self.product_code} - {self.brand_name.generic_name} ({self.generic_name_dosage}) - Batch {self.batch.batch_number}"

    def save(self, *args, **kwargs):
        # Assign a product code only if it hasn't been set
        if not self.product_code:
            # Check if a product with the same brand_name exists
            existing_product = Product.objects.filter(brand_name=self.brand_name).first()
            if existing_product:
                # Reuse the product code from the existing product
                self.product_code = existing_product.product_code
            else:
                # Generate a new product code
                last_product = Product.objects.order_by('id').last()
                if last_product and last_product.product_code.startswith("GCP"):
                    last_number = int(last_product.product_code[3:])  # Extract the numeric part
                    self.product_code = f"GCP{last_number + 1:04d}"  # Increment and format
                else:
                    self.product_code = "GCP0001"  # Start from GCP0001

        # Save the product instance
        super().save(*args, **kwargs)
