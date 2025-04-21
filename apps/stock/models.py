from django.db import models
from django.utils.timezone import now
from apps.products.models import Batch, Product
from apps.branches.models import Branch
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
