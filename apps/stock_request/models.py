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

            # Assemble the prefix with the date included
            prefix = f"REQ-{reg_part}-CWH-{date_part}"

            # Find the latest request number for this branch (ignoring the date)
            latest_request = StockRequest.objects.filter(request_number__icontains=f"REQ-{reg_part}-CWH").order_by('-request_number').first()

            if latest_request:
                # Extract the numeric part of the sequence and increment it
                latest_sequence = int(latest_request.request_number.split("-")[-1])
                sequence = latest_sequence + 1
            else:
                # Start from 1 if no existing requests match the branch
                sequence = 1

            # Assign the new request number
            self.request_number = f"{prefix}-{sequence:05d}"  # Zero-padded to 5 digits

        super().save(*args, **kwargs)




class StockRequestProduct(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.product} for Request #{self.stock_request.id}"


class InTransit(models.Model):
    STATUS_CHOICES = [
    ('In Transit', 'In Transit'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
]
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE, related_name='in_transit', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    source = models.CharField(max_length=255)  # Central Warehouse or Branch ID
    destination = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
    max_length=50,
    choices=STATUS_CHOICES,
    default="In Transit",
)
    

    def __str__(self):
        return f"In-Transit {self.quantity} of {self.product} to {self.destination.branch_name}"
