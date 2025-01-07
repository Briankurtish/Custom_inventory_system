from django.db import models
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from apps.stock.models import Stock
from django.utils.text import slugify
import datetime
from django.utils import timezone

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name='sales_rep_orders'
    )
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
    approved_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who approved the purchase order", related_name='approved_orders'
    )
    notes = models.TextField(
        null=True, blank=True,
        help_text="Optional notes for rejection or other updates"
    )
    purchase_order_id = models.CharField(
        max_length=50, unique=True, editable=False, null=True, blank=True,
        help_text="Unique identifier for the purchase order"
    )

    def save(self, *args, **kwargs):
        if not self.purchase_order_id:
            current_date = timezone.now()
            date_part = current_date.strftime("%Y%m%d")  # Format date as YYYYMMDD

            # Extract the REG part from the branch ID
            branch_id_parts = self.branch.branch_id.split("-")
            reg_part = branch_id_parts[0] if len(branch_id_parts) > 0 else "UNKNOWN"

            # Assemble the prefix with the date included
            prefix = f"PO-{reg_part}-{date_part}"

            # Find the latest purchase order for this branch (ignoring the date)
            latest_order = PurchaseOrder.objects.filter(purchase_order_id__icontains=f"PO-{reg_part}-{date_part}").order_by('-purchase_order_id').first()

            if latest_order:
                # Extract the numeric part of the sequence and increment it
                latest_sequence = int(latest_order.purchase_order_id.split("-")[-1])
                sequence = latest_sequence + 1
            else:
                # Start from 1 if no existing orders match the branch
                sequence = 1

            # Assign the new purchase order ID
            self.purchase_order_id = f"{prefix}-{sequence:05d}"  # Zero-padded to 5 digits

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_order_id} - {self.branch.branch_name}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    temp_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_effective_price(self):
        """Returns the temporary price if set, otherwise the stock product price."""
        return self.temp_price if self.temp_price else self.stock.product.unit_price

    def get_unit_price(self):
        """Returns the unit price of the associated product."""
        return self.stock.product.unit_price

    def get_total_price(self):
        """Returns the total price for the quantity of this item."""
        return self.get_unit_price() * self.quantity


class TemporaryStock(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="temp_stocks")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    ordered_quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock.product.generic_name_dosage} - Ordered: {self.ordered_quantity}"


class Invoice(models.Model):
    
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Payment Ongoing', 'Payment Ongoing'),
        ('Payment Completed', 'Payment Completed'),
    ]
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name='invoice_sales_rep_orders'
    )
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Worker who created this invoice",
        related_name='invoice_created_by_orders'
    )
    purchase_order = models.OneToOneField(
        PurchaseOrder,
        on_delete=models.CASCADE,
        help_text="Associated purchase order",
        null=True,
        blank=True
    )
    invoice_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Unique ID for the invoice"
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount of the invoice"
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount paid by the customer"
    )
    amount_due = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount remaining to be paid"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Unpaid',
        help_text="Current payment status of the invoice"
    )

    def __str__(self):
        return f"Invoice #{self.invoice_id} - {self.branch.branch_name}"

    def generate_invoice_id(self):
        """
        Generate the invoice ID in the format: INV-REG-POxxxxx-YYYY,
        ensuring that the last 5 digits of the invoice match the purchase order.
        """
        if not self.purchase_order or not self.purchase_order.purchase_order_id:
            raise ValueError("Purchase order must be associated with the invoice.")

        # Extract branch region from the purchase order ID (e.g., "BCH" from "PO-BCH-...")
        reg = self.purchase_order.purchase_order_id.split('-')[1]

        # Extract the last 5 digits of the purchase order ID sequence
        po_sequence = self.purchase_order.purchase_order_id.split('-')[-1]

        # Use the current year or creation year for the invoice
        year = self.created_at.year if self.created_at else datetime.datetime.now().year

        # Return the correctly formatted invoice ID
        return f"INV-{reg}-PO{po_sequence}-{year}"

    def save(self, *args, **kwargs):
        # Generate invoice ID if not set
        if not self.invoice_id:
            self.invoice_id = self.generate_invoice_id()
        # Ensure amount due is correctly calculated
        self.amount_due = self.grand_total - self.amount_paid
        super().save(*args, **kwargs)



class InvoiceOrderItem(models.Model):
    invoice_order = models.ForeignKey(
        Invoice, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Price per unit of the product at the time of invoice"
    )

    def __str__(self):
        return f"{self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_total_price(self):
        """
        Returns the total price for the quantity of this item.
        """
        return self.price * self.quantity



class InvoicePayment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name="invoice_payment",
        help_text="The invoice associated with this payment"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid in this transaction")
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, help_text="Mode of payment used")
    payment_date = models.DateTimeField(auto_now_add=True)
    account_paid_to = models.CharField(max_length=255, help_text="Account or entity where the payment was sent")
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the invoice")

    def __str__(self):
        return f"Payment #{self.payment_number} for Invoice #{self.invoice.id}"
    
    

class Receipt(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Credit', 'Credit'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='receipts',
        help_text="Invoice associated with this receipt"
    )
    receipt_id = models.CharField(
        max_length=50, unique=True, editable=False,
        help_text="Unique identifier for the receipt"
    )
    payment_date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the payment was made"
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Amount paid for this receipt"
    )
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHODS,
        help_text="Payment method used for this receipt"
    )
    notes = models.TextField(
        null=True, blank=True, help_text="Optional notes for the receipt"
    )

    def generate_receipt_id(self):
        """
        Generate the receipt ID in the format: RCT-REG-YYYYMMDD-NNNNN
        """
        if not self.invoice or not self.invoice.invoice_id:
            raise ValueError("An invoice must be associated with the receipt.")

        # Extract branch region from the invoice ID (e.g., "REG" from "INV-REG-...")
        reg = self.invoice.invoice_id.split('-')[1]

        # Current date in YYYYMMDD format
        date_part = timezone.now().strftime("%Y%m%d")

        # Find the latest receipt for this branch (ignoring the date)
        last_receipt = Receipt.objects.filter(receipt_id__icontains=f"RCT-{reg}-").order_by('-receipt_id').first()

        if last_receipt:
            # Extract and increment the last sequence number
            last_sequence = int(last_receipt.receipt_id.split('-')[-1])
            sequence = last_sequence + 1
        else:
            # Start sequence at 1 if no receipts exist
            sequence = 1

        # Generate the new receipt ID
        return f"RCT-{reg}-{date_part}-{sequence:05d}"

    def save(self, *args, **kwargs):
        if not self.receipt_id:
            self.receipt_id = self.generate_receipt_id()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Receipt {self.receipt_id} for Invoice {self.invoice.invoice_id}"
