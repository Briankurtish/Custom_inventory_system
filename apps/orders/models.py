from django.db import models
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from apps.stock.models import Stock
from django.utils.text import slugify
import datetime


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
            # Ensure the branch is valid and has a branch_id
            if self.branch and isinstance(self.branch.branch_id, str):
                reg = self.branch.branch_id[:3].upper()
            else:
                reg = "UNK"  # Default region if branch is missing or invalid

            # Use the current date for the date portion
            from datetime import date
            date_str = date.today().strftime("%Y%m%d")

            # Get the total number of orders to generate a unique sequence
            last_order = PurchaseOrder.objects.filter(
                purchase_order_id__startswith=f"PO-{reg}-{date_str}-"
            ).order_by('id').last()

            if last_order and last_order.purchase_order_id:
                # Increment the sequence based on the last order
                last_sequence = int(last_order.purchase_order_id.split('-')[-1])
                new_sequence = last_sequence + 1
            else:
                # Start from 1
                new_sequence = 1

            # Construct the new purchase order ID
            self.purchase_order_id = f"PO-{reg}-{date_str}-{new_sequence:05d}"

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