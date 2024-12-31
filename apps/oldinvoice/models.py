from django.db import models
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from apps.stock.models import Stock
from datetime import timedelta
from django.utils.timezone import now


class OldInvoiceOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name='old_invoice_sales_rep_orders'  # Unique related_name
    )
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')]
    )
    created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when the invoice was created"
    )
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Worker who created this order",
        related_name='old_invoice_created_by_orders'  # Unique related_name
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount of the purchase order"
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount paid by the customer"
    )
    amount_due = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount remaining to be paid"
    )
   

    def __str__(self):
        return f"Order #{self.id} - {self.branch.branch_name} by {self.created_by.user.username if self.created_by else 'Unknown'}"

    def calculate_grand_total(self):
        """
        Calculates and updates the grand total for the order.
        """
        total = sum(item.get_total_price() for item in self.items.all())
        self.grand_total = total
        self.calculate_amount_due()
        self.save(update_fields=["grand_total", "amount_due"])
        return total

    def save(self, *args, **kwargs):
        # Calculate amount due
        self.amount_due = self.grand_total - self.amount_paid

        super().save(*args, **kwargs)




class OldInvoiceOrderItem(models.Model):
    invoice_order = models.ForeignKey(
        OldInvoiceOrder, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_total_price(self):
        """
        Returns the total price for the quantity of this item.
        """
        return self.price() * self.quantity



class InvoicePaymentHistory(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    invoice = models.ForeignKey(
        OldInvoiceOrder, 
        on_delete=models.CASCADE, 
        related_name="payment_history",
        help_text="The invoice associated with this payment"
    )
    payment_date = models.DateTimeField( null=True, blank=True, help_text="Date and time of the payment")
    payment_number = models.CharField(max_length=100, help_text="Unique identifier for the payment")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid in this transaction")
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, help_text="Mode of payment used")
    account_paid_to = models.CharField(max_length=255, help_text="Account or entity where the payment was sent")
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the invoice")

    def __str__(self):
        return f"Payment #{self.payment_number} for Invoice #{self.invoice.id}"
