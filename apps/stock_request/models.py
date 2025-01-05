from django.db import models
from apps.products.models import Product
from apps.branches.models import Branch
from django.contrib.auth.models import User
from django.utils.timezone import now

class StockRequest(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")
    picking_list = models.FileField(upload_to='picking_lists/', null=True, blank=True)
    request_number = models.CharField(max_length=50, unique=True, editable=False)  # Adjusted length for new format

    def __str__(self):
        return f"Stock Request #{self.request_number} by {self.requested_by}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            current_date = now()
            date_part = current_date.strftime("%Y%m%d")  # Format date as YYYYMMDD
            
            # Extract the REG part from the branch ID
            branch_id_parts = self.branch.branch_id.split("-")
            reg_part = branch_id_parts[0] if len(branch_id_parts) > 0 else "UNKNOWN"

            # Assemble the prefix
            prefix = f"REQ-{reg_part}-CWH-{date_part}"

            # Count requests for the same branch and date
            same_day_requests = StockRequest.objects.filter(
                branch=self.branch,
                requested_at__date=current_date.date()
            ).count()

            sequence = same_day_requests + 1  # Start numbering from 1 each day
            self.request_number = f"{prefix}-{sequence:05d}"  # Zero-padded to 5 digits

        super().save(*args, **kwargs)


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
