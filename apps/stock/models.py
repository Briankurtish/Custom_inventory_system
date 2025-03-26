from django.db import models
from django.utils.timezone import now
from apps.products.models import Product
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
    quantity = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        unique_together = ("product", "branch")  # Ensure one record per product per branch

    def __str__(self):
        return f"{self.product.product_code} at {self.branch.branch_name} - {self.quantity} units"


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
        max_length=10,
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
