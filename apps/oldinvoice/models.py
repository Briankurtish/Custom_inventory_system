from django.db import models
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.orders.models import BankDeposit, Check, MomoInfo
from apps.products.models import Product
from apps.workers.models import Worker
from apps.stock.models import Stock
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Max
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class OldInvoiceOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    old_invoice_id = models.CharField(
        max_length=50, unique=True, null=True,
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
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



class OldInvoiceAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Created"),
        ("payment", "Payment Made"),
        ("delet", "Deleted"),

    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='old_invoice_log_created'
    )
    old_invoice = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    branch = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.generic_name} on {self.timestamp}"




class OldInvoiceOrderItem(models.Model):
    invoice_order = models.ForeignKey(
        OldInvoiceOrder, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.product_code} - {self.product.brand_name} (x{self.quantity})"

    def get_total_price(self):
        """
        Returns the total price for the quantity of this item.
        """
        return self.price * self.quantity



class InvoicePaymentHistory(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Deposit', 'Bank Deposit'),
        ('Check', 'Check'),
    ]

    invoice = models.ForeignKey(
        OldInvoiceOrder,
        on_delete=models.CASCADE,
        related_name="old_invoice_payment",
        help_text="The old invoice associated with this payment"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid in this transaction")
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, help_text="Mode of payment used")
    payment_date = models.DateTimeField(null=True)
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the invoice")

    # Store the related payment account based on the mode of payment
    momo_account = models.ForeignKey(
        MomoInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_momo_payments"
    )
    check_account = models.ForeignKey(
        Check, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_check_payments"
    )
    bank_deposit_account = models.ForeignKey(
        BankDeposit, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_deposit_payments"
    )

    installment_number = models.PositiveIntegerField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Invoice Payment History"
        verbose_name_plural = "Invoice Payment Histories"
        ordering = ['installment_number']

    def save(self, *args, **kwargs):
        """
        Auto-increment the installment number for each invoice if it's a new entry.
        """
        if not self.id and self.invoice:
            last_installment = InvoicePaymentHistory.objects.filter(invoice=self.invoice).aggregate(
                Max('installment_number')
            )['installment_number__max']

            self.installment_number = (last_installment or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Installment #{self.installment_number} - Invoice #{self.invoice.id}"
