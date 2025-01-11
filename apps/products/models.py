from django.db import models
from django.db import IntegrityError
from apps.genericName.models import GenericName


class Batch(models.Model):
    batch_number = models.CharField(
        max_length=50, unique=True
    )
    generic_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name='batches'
    )
    expiry_date = models.DateField(help_text="Expiry Date")
    
    def __str__(self):
        return f"Batch: {self.batch_number} -- {self.generic_name.generic_name} - Expiry: {self.expiry_date}"



class Product(models.Model):
    product_code = models.CharField(
        max_length=50, blank=True
    )
    brand_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="brand_products")
    generic_name_dosage = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="dosage_products", null=True, blank=True
    )
    pack_size = models.ForeignKey(
        "pack_size.PackSize", on_delete=models.CASCADE, related_name="products")
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,  # Default value for unit_price
        
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="products"
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
                # Get the last product with a code starting with "PROD"
                last_product = Product.objects.filter(product_code__startswith="PROD").order_by('id').last()
                if last_product:
                    # Extract the numeric part safely
                    try:
                        last_number = int(last_product.product_code.split("-")[1])  # Extract numeric part
                        self.product_code = f"PROD-{last_number + 1:04d}"  # Increment and format
                    except (IndexError, ValueError):
                        # Fallback to starting from PROD-0001 if the code is malformed
                        self.product_code = "PROD-0001"
                else:
                    # Start from PROD-0001 if no product exists
                    self.product_code = "PROD-0001"

        # Save the product instance
        super().save(*args, **kwargs)
