from django.db import models
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from apps.stock.models import Stock


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='sales_rep_orders')
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True, 
        help_text="Worker who created this order", related_name='created_by_orders'
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending', 
        help_text="Current status of the purchase order"
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount of the purchase order"
    )

    def __str__(self):
        return f"Order #{self.id} - {self.branch.branch_name} by {self.created_by.user.username if self.created_by else 'Unknown'}"




class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_unit_price(self):
        """
        Returns the unit price of the associated product.
        """
        return self.stock.product.unit_price

    def get_total_price(self):
        """
        Returns the total price for the quantity of this item.
        """
        return self.get_unit_price() * self.quantity
