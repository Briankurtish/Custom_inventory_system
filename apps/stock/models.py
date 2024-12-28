from django.db import models
from django.utils.timezone import now
from apps.products.models import Product
from apps.branches.models import Branch

class Stock(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name="stocks", 
        help_text="Product associated with this stock"
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name="stocks", 
        help_text="Branch where this stock is stored"
    )
    quantity = models.PositiveIntegerField(
        default=0, 
        help_text="Quantity of stock at this branch"
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
        help_text="Product involved in the transaction"
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name="transactions", 
        help_text="Branch where the transaction occurred"
    )
    transaction_type = models.CharField(
        max_length=10, 
        choices=TRANSACTION_TYPES, 
        help_text="Type of transaction"
    )
    quantity = models.IntegerField(
        help_text="Quantity added, updated, or removed"
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date and time of the transaction"
    )

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.product_code} at {self.branch.branch_name} ({self.quantity})"
