from django.db import models
from django.db import IntegrityError
from apps.genericName.models import GenericName
from apps.workers.models import Worker


class Batch(models.Model):
    batch_number = models.CharField(
        max_length=50, null=True
    )
    generic_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name='batches'
    )
    bl_number = models.CharField(
        max_length=255, blank=True
    )
    prod_date = models.DateField(null=True, blank=True, help_text="Manufacturing Date")

    expiry_date = models.DateField(help_text="Expiration Date", null=True, blank=True)

    batch_date_added = models.DateField(
        auto_now_add=True, null=True
    )

    batch_created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='batches_created'
    )

    def __str__(self):
        return f"Batch: {self.batch_number} -- {self.generic_name.generic_name} - Expiry: {self.expiry_date}"


class BatchAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='batch_log_created'
    )
    batch_number = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.batch_number} on {self.timestamp}"


class DosageForm(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")

    def __str__(self):
        return self.name


class DosageType(models.Model):
    dosage_form = models.ForeignKey(
        DosageForm,
        on_delete=models.CASCADE,
        related_name='dosage_types'
    )
    name = models.CharField(max_length=100, verbose_name="Subcategory Name")

    class Meta:
        unique_together = ['dosage_form', 'name']

    def __str__(self):
        return f"{self.dosage_form.name} - {self.name}"



class Product(models.Model):
    product_code = models.CharField(
        max_length=50, blank=True
    )
    brand_name = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="brand_products", blank=True, null=True)
    generic_name_dosage = models.ForeignKey(
        GenericName, on_delete=models.CASCADE, related_name="dosage_products", null=True, blank=True
    )
    dosage_form = models.ForeignKey(
        DosageForm, on_delete=models.CASCADE, related_name="products",
        null=True, blank=True, verbose_name="Dosage Form"
    )
    dosage_type = models.ForeignKey(
        DosageType, on_delete=models.CASCADE, related_name="products",
        null=True, blank=True, verbose_name="Dosage Type"
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

    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products_created'
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )


    class Meta:
        unique_together = ("brand_name", "batch")  # Ensure each brand_name and batch combination is unique

    def __str__(self):
        brand_name = self.brand_name.brand_name if self.brand_name else 'No Brand'
        return f"{self.product_code} - ({brand_name}) --  ({self.generic_name_dosage}) - Batch - {self.batch.batch_number}"


    def save(self, *args, **kwargs):
        # Assign a product code only if it hasn't been set
        if not self.product_code:
            # Check if a product with the same brand_name and generic_name_dosage exists
            existing_product = Product.objects.filter(
                brand_name=self.brand_name,
                generic_name_dosage=self.generic_name_dosage
            ).exclude(id=self.id).first()

            if existing_product:
                # Reuse the product_code from the existing product
                self.product_code = existing_product.product_code
            else:
                # Find the highest numeric part of all existing product_codes
                highest_number = 0
                all_products = Product.objects.filter(product_code__startswith="PROD")
                for product in all_products:
                    try:
                        number = int(product.product_code.split("-")[1])
                        highest_number = max(highest_number, number)
                    except (IndexError, ValueError):
                        continue

                # Increment the highest number to generate a new product_code
                new_number = highest_number + 1
                new_code = f"PROD-{new_number:04d}"

                # Ensure the new product_code doesn't conflict with existing codes for different brand_name/generic_name_dosage
                while Product.objects.filter(product_code=new_code).exclude(
                    brand_name=self.brand_name, generic_name_dosage=self.generic_name_dosage
                ).exclude(id=self.id).exists():
                    new_number += 1
                    new_code = f"PROD-{new_number:04d}"

                self.product_code = new_code

        # Save the product instance
        super().save(*args, **kwargs)


class ProductAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("update_price", "Update Price"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='product_log_created'
    )
    generic_name = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.generic_name} on {self.timestamp}"
