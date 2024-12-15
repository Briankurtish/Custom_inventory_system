from django.db import models
from apps.products.models import Product
from apps.branches.models import Branch
from django.contrib.auth.models import User

# Create your models here.
class StockRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")  # Ensure this field exists

    def __str__(self):
        return f"Request for {self.product} by {self.requested_by}"
