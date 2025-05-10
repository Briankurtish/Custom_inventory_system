from django.db import models
from django.utils.timezone import now
from apps.products.models import Batch, Product
from apps.branches.models import Branch
from apps.stock_request.models import StockRequest, StockTransfer
from apps.workers.models import Worker

class Stock(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stocks"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="stocks"
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stocks"
    )  # Added batch field
    quantity = models.PositiveIntegerField(
        default=0
    )
    total_inventory = models.PositiveIntegerField(
        default=0
    )
    begining_inventory = models.PositiveIntegerField(
        default=0, null=True
    )
    fixed_beginning_inventory = models.PositiveIntegerField(
        default=0, null=True, editable=False
    )
    quantity_transferred = models.PositiveIntegerField(
        default=0
    )
    return_quantity = models.PositiveIntegerField(default=0)
    damaged_quantity = models.PositiveIntegerField(default=0)
    samples_quantity = models.PositiveIntegerField(default=0)
    total_sold = models.PositiveIntegerField(
        default=0
    )
    total_stock = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_created'
    )
    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    class Meta:
        unique_together = ("product", "branch", "batch")  # Updated to include batch

    def __str__(self):
        batch_info = self.batch.batch_number if self.batch else "No Batch"
        return f"{self.product.product_code} at {self.branch.branch_name} - {self.quantity} units - Batch: {batch_info}"

    # def save(self, *args, **kwargs):
    #     """ Automatically update total_stock and fixed_beginning_inventory before saving """
    #     # Set fixed_beginning_inventory only once (if it's not already set)
    #     if not self.fixed_beginning_inventory:
    #         self.fixed_beginning_inventory = self.begining_inventory

    #     # Update beginning_inventory to match fixed_beginning_inventory
    #     self.begining_inventory = self.fixed_beginning_inventory

    #     self.total_inventory = (self.fixed_beginning_inventory or 0) + self.quantity

    #     # Update total_stock to reflect available stock after transfers
    #     self.total_stock = self.total_inventory - self.quantity_transferred

    #     super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("ADD", "Add Stock"),
        ("UPDATE", "Update Stock"),
        ("REMOVE", "Remove Stock"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=255,
        choices=TRANSACTION_TYPES
    )
    quantity = models.IntegerField()
    transaction_date = models.DateTimeField(
        auto_now_add=True,
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,  # If the worker is deleted, keep the transaction but set worker to NULL
        null=True,
        blank=True,
        related_name="inventory_transactions",
    )

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.product_code} at {self.branch.branch_name} ({self.quantity}) by {self.worker if self.worker else 'Unknown'}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("REQUEST", "Stock Request"),
        ("TRANSFER", "Stock Transfer"),
    ]

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        verbose_name="Movement Type",
        help_text="Whether this is a stock request or transfer."
    )
    stock_request = models.ForeignKey(
        StockRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name="Stock Request",
        help_text="The stock request associated with this movement, if applicable."
    )
    stock_transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name="Stock Transfer",
        help_text="The stock transfer associated with this movement, if applicable."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Product",
        help_text="The product associated with this stock movement.",
        null=True,
        blank=True,

    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantity",
        help_text="The quantity of the product moved in this stock movement.",
        null=True,
        blank=True,
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Batch",
        help_text="The batch associated with this movement, if applicable."
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Transaction Date",
        help_text="The date the stock movement was recorded."
    )

    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ["-transaction_date"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(stock_request__isnull=False, stock_transfer__isnull=True) |
                    models.Q(stock_request__isnull=True, stock_transfer__isnull=False)
                ),
                name="one_movement_type_only"
            )
        ]

    def __str__(self):
        if self.movement_type == "REQUEST" and self.stock_request:
            return f"Stock Request #{self.stock_request.id} - {self.product} ({self.quantity}) on {self.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}"
        elif self.movement_type == "TRANSFER" and self.stock_transfer:
            return f"Stock Transfer #{self.stock_transfer.id} - {self.product} ({self.quantity}) on {self.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"{self.get_movement_type_display()} (Invalid) - {self.product} ({self.quantity}) on {self.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}"

class DamagedProduct(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="damaged_products"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="damaged_products"
    )
    quantity = models.PositiveIntegerField(
        help_text="Quantity of damaged products"
    )
    date_recorded = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when the damage was recorded"
    )
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='damaged_products_created'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes about the damage"
    )

    class Meta:
        verbose_name = "Damaged Product"
        verbose_name_plural = "Damaged Products"
        ordering = ["-date_recorded"]

    def __str__(self):
        return f"{self.product.generic_name} - {self.quantity} damaged at {self.branch.branch_name} on {self.date_recorded.strftime('%Y-%m-%d')}"

    @property
    def generic_name(self):
        return self.product.generic_name

    @property
    def brand_name(self):
        return self.product.brand_name

    @property
    def dosage_form(self):
        return self.product.dosage_form
