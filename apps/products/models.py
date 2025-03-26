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
            if self.brand_name:
                # If brand_name is provided, check for existing products with the same brand_name
                existing_product = Product.objects.filter(brand_name=self.brand_name).first()
                if existing_product:
                    # Reuse the product code from the existing product
                    self.product_code = existing_product.product_code
                else:
                    # Generate a new product code for the brand
                    last_product = Product.objects.filter(product_code__startswith="PROD").order_by('id').last()
                    if last_product:
                        try:
                            last_number = int(last_product.product_code.split("-")[1])  # Extract numeric part
                            self.product_code = f"PROD-{last_number + 1:04d}"  # Increment and format
                        except (IndexError, ValueError):
                            # Fallback to starting from PROD-0001 if the code is malformed
                            self.product_code = "PROD-0001"
                    else:
                        # Start from PROD-0001 if no product exists
                        self.product_code = "PROD-0001"
            else:
                # If brand_name is empty, use generic_name_dosage to generate the product code
                if self.generic_name_dosage:
                    # Check for existing products with the same generic_name_dosage and no brand_name
                    existing_product = Product.objects.filter(
                        generic_name_dosage=self.generic_name_dosage,
                        brand_name__isnull=True
                    ).first()
                    if existing_product:
                        # Reuse the product code from the existing product
                        self.product_code = existing_product.product_code
                    else:
                        # Generate a new product code for the generic_name_dosage
                        last_product = Product.objects.filter(product_code__startswith="PROD").order_by('id').last()
                        if last_product:
                            try:
                                last_number = int(last_product.product_code.split("-")[1])  # Extract numeric part
                                self.product_code = f"PROD-{last_number + 1:04d}"  # Increment and format
                            except (IndexError, ValueError):
                                # Fallback to starting from PROD-0001 if the code is malformed
                                self.product_code = "PROD-0001"
                        else:
                            # Start from PROD-0001 if no product exists
                            self.product_code = "PROD-0001"
                else:
                    # If both brand_name and generic_name_dosage are empty, generate a unique product code
                    last_product = Product.objects.filter(product_code__startswith="PROD").order_by('id').last()
                    if last_product:
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
