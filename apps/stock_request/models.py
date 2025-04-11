from datetime import datetime, timezone
from django.db import models
from apps.products.models import Batch, Product
from apps.branches.models import Branch
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Max
from apps.workers.models import Worker
import re

from django.utils import timezone
import re

class StockRequest(models.Model):
    SURPLUS = "Surplus"
    DEFICIT = "Deficit"
    NORMAL = "Normal"

    REQUEST_TYPE_CHOICES = [
        (SURPLUS, "Surplus"),
        (DEFICIT, "Deficit"),
        (NORMAL, "Normal"),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name="requested_stock_requests"
    )
    requested_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=50, default="Pending")
    picking_list = models.FileField(upload_to="picking_lists/", null=True, blank=True)
    request_number = models.CharField(max_length=50, unique=True, editable=False)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES, default=NORMAL)

    def __str__(self):
        return f"Stock Request #{self.request_number} by {self.requested_by} ({self.request_type})"

    def save(self, *args, **kwargs):
        if not self.request_number:
            # Ensure requested_at is a valid datetime
            if isinstance(self.requested_at, str):
                try:
                    self.requested_at = timezone.datetime.fromisoformat(self.requested_at)
                except ValueError:
                    self.requested_at = timezone.now()

            # Format the date as YYYYMMDD
            date_part = self.requested_at.strftime("%Y%m%d") if self.requested_at else timezone.now().strftime("%Y%m%d")

            # Extract the branch prefix (e.g., BAF from BAF-01)
            branch_id_parts = self.branch.branch_id.split("-")
            reg_part = branch_id_parts[0] if len(branch_id_parts) > 0 else "UNKNOWN"

            # Generate the prefix (WITH date, WITHOUT sequence number)
            prefix = f"REQ-{reg_part}-CWH-{date_part}"

            # Get the highest existing sequence number (GLOBAL, IGNORING DATE & BRANCH)
            latest_request = StockRequest.objects.order_by('-id').first()

            if latest_request and latest_request.request_number:
                # Extract the last 5-digit sequence number
                match = re.search(r"-(\d{5})$", latest_request.request_number)
                latest_sequence = int(match.group(1)) if match else 0
            else:
                latest_sequence = 0

            # Increment the global sequence number
            new_sequence = latest_sequence + 1

            # Assign new request number (zero-padded to 5 digits)
            self.request_number = f"{prefix}-{new_sequence:05d}"

        super().save(*args, **kwargs)


# current_date = now()
# # date_part = current_date.strftime("%Y%m%d")  # YYYYMMDD format


class StockTransfer(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Received", "Received"),
        ("Cancelled", "Cancelled"),
    ]
    transfer_type = models.CharField(max_length=20, choices=[("Regular", "Regular"), ("Surplus", "Surplus"), ("Deficit", "Deficit")], default="Regular")
    transfer_id = models.CharField(max_length=50, unique=True, editable=False)
    source_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="transfers_from"
    )
    destination_branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="transfers_to"
    )
    transferred_by = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name="transfers_made"
    )
    date_transferred = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    def __str__(self):
        return f"Transfer #{self.transfer_id} from {self.source_branch} to {self.destination_branch}"

    def save(self, *args, **kwargs):
        if not self.transfer_id:
            # Handle date_transferred as string or datetime
            if self.date_transferred:
                if isinstance(self.date_transferred, str):
                    # Convert string (e.g., "2025-04-08") to datetime
                    date_transferred = datetime.strptime(self.date_transferred, "%Y-%m-%d")
                else:
                    # Already a datetime object
                    date_transferred = self.date_transferred
            else:
                # Use current time if None
                date_transferred = timezone.now()

            # Format the date as YYYYMMDD
            date_part = date_transferred.strftime("%Y%m%d")

            # Extract branch prefixes
            source_prefix = self.source_branch.branch_id.split("-")[0] if "-" in self.source_branch.branch_id else "UNKNOWN"
            dest_prefix = self.destination_branch.branch_id.split("-")[0] if "-" in self.destination_branch.branch_id else "UNKNOWN"

            # Generate the prefix
            prefix = f"TRF-{source_prefix}-{dest_prefix}-{date_part}"

            # Get the latest sequence number
            latest_transfer = StockTransfer.objects.order_by('-id').first()
            latest_sequence = int(re.search(r"-(\d{5})$", latest_transfer.transfer_id).group(1)) if latest_transfer and latest_transfer.transfer_id and re.search(r"-(\d{5})$", latest_transfer.transfer_id) else 0
            new_sequence = latest_sequence + 1

            # Assign new transfer ID
            self.transfer_id = f"{prefix}-{new_sequence:05d}"

        super().save(*args, **kwargs)

class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    actual_quantity_received = models.PositiveIntegerField(null=True, blank=True)
    surplus = models.PositiveIntegerField(default=0)
    deficit = models.PositiveIntegerField(default=0)
    date_received = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.product} - {self.quantity} (Batch: {self.batch.batch_number if self.batch else 'No Batch'})"


class StockRequestDocument(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ('Picking List', 'Picking List'),
        ('Transfer Slip', 'Transfer Slip'),
        ('Goods Receipt Note', 'Goods Receipt Note'),
    ])
    document = models.FileField(upload_to='stock_request_documents/', null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who uploaded document", related_name='stock_request_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"



class StockTransferDocument(models.Model):
    stock_transfer = models.ForeignKey(
        'StockTransfer',  # Replace 'StockTransfer' with the actual model name if different
        on_delete=models.CASCADE,
        related_name="documents"
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('Picking List', 'Picking List'),
            ('Transfer Slip', 'Transfer Slip'),
            ('Goods Receipt Note', 'Goods Receipt Note'),
        ]
    )
    document = models.FileField(
        upload_to='stock_transfer_documents/',
        null=True
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        null=True
    )
    uploaded_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Worker who uploaded document",
        related_name='stock_transfer_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"

    class Meta:
        verbose_name = "Stock Transfer Document"
        verbose_name_plural = "Stock Transfer Documents"



class StockRequestProduct(models.Model):
    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)  # Store the batch

    def __str__(self):
        return f"{self.product} - {self.quantity} (Batch: {self.batch.batch_number if self.batch else 'No Batch'})"


class InTransit(models.Model):
    STATUS_CHOICES = [
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    stock_request = models.ForeignKey(StockRequest, on_delete=models.CASCADE, related_name='in_transit', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    actual_quantity_received = models.PositiveIntegerField(null=True, blank=True)
    surplus = models.PositiveIntegerField(default=0)
    deficit = models.PositiveIntegerField(default=0)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)  # Added batch field
    source = models.CharField(max_length=255)  # Central Warehouse or Branch ID
    destination = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_at = models.DateTimeField(null=True)
    date_received = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="In Transit",
    )

    def save(self, *args, **kwargs):
        # Auto-calculate surplus and deficit before saving
        if self.actual_quantity_received is not None:
            if self.actual_quantity_received > self.quantity:
                self.surplus = self.actual_quantity_received - self.quantity
                self.deficit = 0
            elif self.actual_quantity_received < self.quantity:
                self.deficit = self.quantity - self.actual_quantity_received
                self.surplus = 0
            else:
                self.surplus = 0
                self.deficit = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"In-Transit {self.quantity} of {self.product} (Batch: {self.batch.batch_number if self.batch else 'N/A'}) to {self.destination.branch_name}"




class StockRequestAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Stock Request Created"),
        ("approve", "Stock Request Approved"),
        ("reject", "Stock Request Rejected"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("surplus", "Surplus"),
        ("deficit", "Deficit"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='request_log_created'
    )
    request = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    branch = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=255, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.request} on {self.timestamp}"




class StockTransferAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Stock Transfer Created"),
        ("complete", "Stock Transfer Completed"),
        ("cancel", "Stock Transfer Cancelled"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("surplus", "Surplus Recorded"),
        ("deficit", "Deficit Recorded"),
    ]

    user = models.ForeignKey(
        'workers.Worker',  # Adjust to your Worker model path if different
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_log_created',
        verbose_name="User"
    )
    transfer = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name= "Transfer ID"
    )
    source_branch = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name= "Source Branch"
    )
    destination_branch = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name= "Destination Branch"
    )
    action = models.CharField(
        max_length=255,
        choices=ACTION_CHOICES,
        verbose_name= "Action"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name= "Timestamp"
    )
    details = models.TextField(
        null=True,
        blank=True,
        verbose_name= "Details"
    )

    def __str__(self):
        return f"{self.user or 'Anonymous'} {self.get_action_display()} {self.transfer or 'N/A'} on {self.timestamp}"

    class Meta:
        verbose_name = "Stock Transfer Audit Log"
        verbose_name_plural = "Stock Transfer Audit Logs"