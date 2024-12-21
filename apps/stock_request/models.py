from django.db import models
from apps.products.models import Product
from apps.branches.models import Branch
from django.contrib.auth.models import User

class StockRequest(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"Stock Request #{self.id} by {self.requested_by}"

class StockRequestProduct(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.product} for Request #{self.stock_request.id}"


class InTransit(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE, related_name='in_transit', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    source = models.CharField(max_length=255)  # Central Warehouse or Branch ID
    destination = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="In Transit")  # Add status field
    

    def __str__(self):
        return f"In-Transit {self.quantity} of {self.product} to {self.destination.branch_name}"
