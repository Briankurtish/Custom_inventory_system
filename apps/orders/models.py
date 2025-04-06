from decimal import Decimal
from django.db import models, transaction
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from apps.stock.models import Stock
from django.utils.text import slugify
import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings



class Bank(models.Model):
    name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    code_agency = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20, unique=True)
    rib = models.CharField(max_length=10)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bank_created'
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    def __str__(self):
        return f"{self.name} - {self.account_name} - {self.bank_code}"


class MomoInfo(models.Model):
    branch = models.ForeignKey(  # Change to ForeignKey
        Branch,  # Reference the Branch model
        on_delete=models.CASCADE,  # Define the deletion behavior
        related_name="momo_infos"  # Optional: related name for reverse access
    )
    master_sim_name = models.CharField(max_length=100)
    master_sim_no = models.CharField(max_length=100)
    momo_number = models.CharField(max_length=15, unique=True)
    momo_name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=100, default="Mobile Money")
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="momo_accounts")
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='momo_created'
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    @property
    def full_account_number(self):
        return f"{self.bank.bank_code}{self.bank.code_agency}{self.bank.account_number}{self.bank.rib}"

    def __str__(self):
        return f"{self.branch} - {self.momo_name} ({self.momo_number})"


class Check(models.Model):
    branch = models.ForeignKey(  # Change to ForeignKey
        Branch,  # Reference the Branch model
        on_delete=models.CASCADE,  # Define the deletion behavior
        related_name="check_infos"  # Optional: related name for reverse access
    )
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="checks")
    payment_type = models.CharField(max_length=100, default="Check")
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='check_created'
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    @property
    def full_account_number(self):
        return f"{self.bank.bank_code}{self.bank.code_agency}{self.bank.account_number}{self.bank.rib}"

    def __str__(self):
        return f"Check - {self.branch} - {self.bank.name}"


class BankDeposit(models.Model):
    branch = models.ForeignKey(  # Change to ForeignKey
        Branch,  # Reference the Branch model
        on_delete=models.CASCADE,  # Define the deletion behavior
        related_name="deposit_infos"  # Optional: related name for reverse access
    )
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="deposits")
    payment_type = models.CharField(max_length=100, default="Bank Deposit")
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deposit_created'
    )

    date_added = models.DateField(
        auto_now_add=True, null=True
    )

    @property
    def full_account_number(self):
        return f"{self.bank.bank_code}{self.bank.code_agency}{self.bank.account_number}{self.bank.rib}"

    def __str__(self):
        return f"Deposit - {self.branch} - {self.bank.name}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Deposit', 'Bank Deposit'),
        ('Check', 'Check'),
    ]

    TAX_RATE_CHOICES = [
        (Decimal("2.0"), "2.0%"),
        (Decimal("2.20"), "2.20%"),
        (Decimal("5.0"), "5.0%"),
        (Decimal("5.50"), "5.50%"),
        (Decimal("0.0"), "0.0%"),
    ]

    PRECOMPTE_CHOICES = [
        (Decimal("2.0"), "2.0%"),
        (Decimal("5.0"), "5.0%"),
        (Decimal("0.0"), "0.0%"),
    ]

    TVA_CHOICES = [
        (Decimal("19.25"), "19.25%"),
        (Decimal("0.0"), "0.0%"),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('Purchase Order', 'Purchase Order'),
        ('Invoice', 'Invoice'),
        ('Receipt', 'Receipt'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker,
        null=True,
        on_delete=models.SET_NULL,
        related_name='sales_rep_orders',
        limit_choices_to={'role': 'Sales Rep'}
    )
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')]
    )
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, null=True)
    created_at = models.DateTimeField(null=True)
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

    old_purchase_order_id = models.CharField(max_length=50, null=True, blank=True)  # New field to store the old ID

    # Store the related payment account based on the mode of payment
    momo_account = models.ForeignKey(
        MomoInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_momo_payments_order"
    )
    check_account = models.ForeignKey(
        Check, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_check_payments_order"
    )
    bank_deposit_account = models.ForeignKey(
        BankDeposit, on_delete=models.SET_NULL, null=True, blank=True, related_name="old_deposit_payments_order"
    )

    tax_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=TAX_RATE_CHOICES, verbose_name="Tax (taux)", default=0.0)
    precompte = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=PRECOMPTE_CHOICES, verbose_name="PreCompte", default=0.0)
    tva = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=TVA_CHOICES, verbose_name="TVA", default=0.0)
    is_special_customer = models.BooleanField(null=True, default=False, verbose_name="Is a Special Customer")

    # document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, null=True)
    # document = models.FileField(upload_to='purchase_order_documents/', null=True)
    # uploaded_at = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        if not self.purchase_order_id:
            # Use the date from created_at or current date
            order_date = self.created_at if self.created_at else timezone.now()
            date_part = order_date.strftime("%Y%m%d")  # Keep date in ID for reference
            
            # Extract REG from branch ID (e.g., "REG" from "REG-001")
            branch_id_parts = self.branch.branch_id.split("-")
            reg_part = branch_id_parts[0] if branch_id_parts else "UNKNOWN"
            
            # Base prefix without sequence (PO-REG-YYYYMMDD-)
            base_prefix = f"PO-{reg_part}-{date_part}-"
            
            # Find the highest existing sequence number ACROSS ALL DATES for this branch
            existing_ids = PurchaseOrder.objects.filter(
                purchase_order_id__startswith=f"PO-{reg_part}-"
            ).values_list('purchase_order_id', flat=True)
            
            # Extract all sequence numbers
            sequences = []
            for po_id in existing_ids:
                try:
                    # Extract last part (sequence number)
                    seq_part = po_id.split("-")[-1]  
                    if seq_part.isdigit():
                        sequences.append(int(seq_part))
                except (IndexError, ValueError):
                    continue
            
            # Determine next sequence number
            sequence = max(sequences) + 1 if sequences else 1
            
            # Format final ID (PO-REG-YYYYMMDD-XXXXX)
            self.purchase_order_id = f"{base_prefix}{sequence:05d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_order_id} - {self.branch.branch_name}"

    # def save(self, *args, **kwargs):
    #     if not self.purchase_order_id:
    #         current_date = timezone.now()
    #         date_part = current_date.strftime("%Y%m%d")  # Format date as YYYYMMDD

    #         # Extract the REG part from the branch ID
    #         branch_id_parts = self.branch.branch_id.split("-")
    #         reg_part = branch_id_parts[0] if len(branch_id_parts) > 0 else "UNKNOWN"

    #         # Assemble the prefix with the date included
    #         prefix = f"PO-{reg_part}-{date_part}"

    #         # Find the latest purchase order for this branch (ignoring the date)
    #         latest_order = PurchaseOrder.objects.filter(purchase_order_id__icontains=f"PO-{reg_part}").order_by('-purchase_order_id').first()

    #         if latest_order:
    #             # Extract the numeric part of the sequence and increment it
    #             latest_sequence = int(latest_order.purchase_order_id.split("-")[-1])
    #             sequence = latest_sequence + 1
    #         else:
    #             # Start from 1 if no existing orders match the branch
    #             sequence = 1

    #         # Assign the new purchase order ID
    #         self.purchase_order_id = f"{prefix}-{sequence:05d}"  # Zero-padded to 5 digits

    #     super().save(*args, **kwargs)

    # def __str__(self):
    #     return f"{self.purchase_order_id} - {self.branch.branch_name}"


class PurchaseOrderDocument(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ('Purchase Order', 'Purchase Order'),
    ])
    document = models.FileField(upload_to='purchase_order_documents/', null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who uploaded document", related_name='purchase_orders_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"


class ReturnPurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Deposit', 'Bank Deposit'),
        ('Check', 'Check'),
    ]

    TAX_RATE_CHOICES = [
        (Decimal("2.0"), "2.0%"),
        (Decimal("2.20"), "2.20%"),
        (Decimal("5.0"), "5.0%"),
        (Decimal("5.50"), "5.50%"),
        (Decimal("0.0"), "0.0%"),
    ]

    PRECOMPTE_CHOICES = [
        (Decimal("2.0"), "2.0%"),
        (Decimal("5.0"), "5.0%"),
        (Decimal("0.0"), "0.0%"),
    ]

    TVA_CHOICES = [
        (Decimal("19.25"), "19.25%"),
        (Decimal("0.0"), "0.0%"),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('Purchase Order', 'Purchase Order'),
        ('Invoice', 'Invoice'),
        ('Receipt', 'Receipt'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker,
        null=True,
        on_delete=models.SET_NULL,
        related_name='return_sales_rep_orders',
        limit_choices_to={'role': 'Sales Rep'}
    )
    original_purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        help_text="Reference to the original purchase order"
    )
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')], null=True, blank=True
    )
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who created this return order", related_name='return_created_by_orders'
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending',
        help_text="Current status of the return purchase order"
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount of the return purchase order"
    )
    approved_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who approved the return purchase order", related_name='return_approved_orders'
    )
    notes = models.TextField(
        null=True, blank=True,
        help_text="Optional notes for rejection or other updates"
    )
    return_order_id = models.CharField(
        max_length=50, unique=True, editable=False, null=True, blank=True,
        help_text="Unique identifier for the return purchase order"
    )

    old_return_order_id = models.CharField(max_length=50, null=True, blank=True)  # New field to store the old ID

    # Store the related payment account based on the mode of payment
    momo_account = models.ForeignKey(
        MomoInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_momo_payments_order"
    )
    check_account = models.ForeignKey(
        Check, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_check_payments_order"
    )
    bank_deposit_account = models.ForeignKey(
        BankDeposit, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_deposit_payments_order"
    )

    tax_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=TAX_RATE_CHOICES, verbose_name="Tax (taux)", default=0.0)
    precompte = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=PRECOMPTE_CHOICES, verbose_name="PreCompte", default=0.0)
    tva = models.DecimalField(max_digits=12, decimal_places=2, null=True, choices=TVA_CHOICES, verbose_name="TVA", default=0.0)
    is_special_customer = models.BooleanField(null=True, default=False, verbose_name="Is a Special Customer")

    def __str__(self):
        return f"Return PO #{self.return_order_id} - {self.branch.branch_name}"


class ReturnPurchaseOrderDocument(models.Model):
    return_purchase_order = models.ForeignKey(ReturnPurchaseOrder, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ('Purchase Order', 'Purchase Order'),
    ])
    document = models.FileField(upload_to='return_purchase_order_documents/', null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who uploaded document", related_name='return_orders_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"


class ReturnPurchaseOrderItem(models.Model):
    return_purchase_order = models.ForeignKey(
        ReturnPurchaseOrder, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    temp_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    return_reason = models.CharField(
        max_length=200,
        null=True, blank=True,
        default="No Note",
        help_text="Reason for return"
    )

    def __str__(self):
        return f"Returned: {self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_effective_price(self):
        """Returns the temporary price if set, otherwise the stock product price."""
        return self.temp_price if self.temp_price else self.stock.product.unit_price

    def get_unit_price(self):
        """Returns the unit price of the associated product."""
        return self.stock.product.unit_price

    def get_total_price(self):
        """Returns the total price for the quantity of this returned item."""
        return self.get_unit_price() * self.quantity



class PaymentSchedule(models.Model):

    WHEN_CHOICES = [
        ('Upon Delivery', 'Upon Delivery'),
        ('1 Week', '1 Week'),
        ('2 Weeks', '2 Weeks'),
        ('3 Weeks', '3 Weeks'),
        ('4 Weeks', '4 Weeks'),
        ('5 Weeks', '5 Weeks'),
        ('6 Weeks', '6 Weeks'),
    ]

    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="purchase_order", on_delete=models.CASCADE
    )
    when = models.CharField(max_length=100, choices=WHEN_CHOICES)
    amount = models.CharField(max_length=100)
    payment_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.when} - {self.amount} - {self.payment_date}"


class ReturnPaymentSchedule(models.Model):

    WHEN_CHOICES = [
        ('Upon Delivery', 'Upon Delivery'),
        ('1 Week', '1 Week'),
        ('2 Weeks', '2 Weeks'),
        ('3 Weeks', '3 Weeks'),
        ('4 Weeks', '4 Weeks'),
        ('5 Weeks', '5 Weeks'),
        ('6 Weeks', '6 Weeks'),
    ]

    return_purchase_order = models.ForeignKey(
        ReturnPurchaseOrder, related_name="return_purchase_order", on_delete=models.CASCADE
    )
    when = models.CharField(max_length=100, choices=WHEN_CHOICES)
    amount = models.CharField(max_length=100)
    payment_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.when} - {self.amount} - {self.payment_date}"


class PurchaseOrderAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("approve", "Approve"),
        ("reject", "Reject"),
        ("Cancel", "Cancel"),
        ("delete", "Delete"),
    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_log_created'
    )
    order = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    branch = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.generic_name} on {self.timestamp}"


class InvoiceAuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Created"),
        ("payment", "Payment Made"),

    ]

    user = models.ForeignKey(
        'workers.Worker', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='invoice_log_created'
    )
    invoice = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    branch = models.CharField(max_length=255, null=True, blank=True)  # Add this line
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)  # To store extra details (e.g., changes)

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.generic_name} on {self.timestamp}"



class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    temp_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reason = models.CharField(
        max_length=200,
        null=True, blank=True,
        default="No Note",
        help_text="Reason for price change"
    )

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
    created_at = models.DateTimeField(null=True)
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

    old_invoice_id = models.CharField(max_length=50, null=True, blank=True)
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount before taxes"
    )
    total_with_taxes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount including taxes"
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

        reg = self.purchase_order.purchase_order_id.split('-')[1]
        po_sequence = self.purchase_order.purchase_order_id.split('-')[-1]
        year = self.created_at.year if self.created_at else datetime.datetime.now().year

        return f"INV-{reg}-PO{po_sequence}-{year}"

    def calculate_total_with_taxes(self):
        """
        Calculate the total invoice amount including applicable taxes.
        """
        if self.purchase_order:
            tax_rate = Decimal(self.purchase_order.tax_rate or 0)
            tva = Decimal(self.purchase_order.tva or 0)
            precompte = Decimal(self.purchase_order.precompte or 0)

            tax_amount = (self.grand_total * tax_rate) / Decimal(100)
            tva_amount = (self.grand_total * tva) / Decimal(100)
            precompte_amount = (self.grand_total * precompte) / Decimal(100)

            if hasattr(self, "is_special_customer") and self.is_special_customer:
                return self.grand_total + tva_amount + precompte_amount
            else:
                return self.grand_total + tva_amount + tax_amount + precompte_amount
        return self.grand_total  # No taxes if no purchase order

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            self.invoice_id = self.generate_invoice_id()

        # Calculate total including taxes
        self.total_with_taxes = self.calculate_total_with_taxes()

        # Calculate amount_due based on total_with_taxes
        self.amount_due = self.total_with_taxes - self.amount_paid

        super().save(*args, **kwargs)


    # def generate_invoice_id(self):
    #     """
    #     Generate the invoice ID:
    #     - If it's a return, use the same sequence as the original invoice but prepend `RET-`.
    #     - Otherwise, follow the normal invoice format.
    #     """
    #     if not self.purchase_order or not self.purchase_order.purchase_order_id:
    #         raise ValueError("Purchase order must be associated with the invoice.")

    #     reg = self.purchase_order.purchase_order_id.split('-')[1]
    #     po_sequence = self.purchase_order.purchase_order_id.split('-')[-1]
    #     year = self.created_at.year if self.created_at else datetime.datetime.now().year

    #     # Check if this is a return (based on a note or other logic)
    #     is_return = self.purchase_order.purchase_order_id.startswith("RET-")

    #     if is_return:
    #         # Use the original invoice ID but prepend RET-
    #         return f"RET-{self.purchase_order.purchase_order_id.replace('PO-', 'INV-')}"
    #     else:
    #         return f"INV-{reg}-PO{po_sequence}-{year}"


class InvoiceDocument(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ('Invoice', 'Invoice'),
    ])
    document = models.FileField(upload_to='invoice_documents/', null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who uploaded document", related_name='invoice_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"



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




class ReturnInvoice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Refunded', 'Refunded'),
        ('Partially Refunded', 'Partially Refunded'),
        ('Rejected', 'Rejected'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name='return_invoice_sales_rep_orders'
    )
    payment_method = models.CharField(
        max_length=50, choices=[('Cash', 'Cash'), ('Credit', 'Credit')], null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who created this return invoice",
        related_name='return_invoice_created_by_orders'
    )
    original_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        help_text="Reference to the original invoice"
    )
    return_purchase_order = models.OneToOneField(
        ReturnPurchaseOrder,
        on_delete=models.CASCADE,
        help_text="Associated return purchase order",
        null=True,
        blank=True
    )
    return_invoice_id = models.CharField(
        max_length=50, unique=True, blank=True,
        help_text="Unique ID for the return invoice"
    )
    old_return_invoice_id = models.CharField(max_length=50, null=True, blank=True)
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount before taxes"
    )
    total_with_taxes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Total amount including taxes"
    )
    amount_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Amount refunded to the customer"
    )
    amount_due = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        help_text="Remaining amount that needs to be refunded"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending',
        help_text="Current refund status of the return invoice"
    )

    def __str__(self):
        return f"Return Invoice #{self.return_invoice_id} - {self.branch.branch_name}"

    def calculate_total_with_taxes(self):
        """
        Calculate the total return invoice amount including applicable taxes.
        """
        if self.return_purchase_order:
            tax_rate = Decimal(self.return_purchase_order.tax_rate or 0)
            tva = Decimal(self.return_purchase_order.tva or 0)
            precompte = Decimal(self.return_purchase_order.precompte or 0)

            tax_amount = (self.grand_total * tax_rate) / Decimal(100)
            tva_amount = (self.grand_total * tva) / Decimal(100)
            precompte_amount = (self.grand_total * precompte) / Decimal(100)

            return self.grand_total + tva_amount + tax_amount + precompte_amount
        return self.grand_total  # No taxes if no return purchase order

    def save(self, *args, **kwargs):
        if not self.return_invoice_id:
           self.return_invoice_id = f"RET-{self.original_invoice.invoice_id}" 

        # Calculate total including taxes
        self.total_with_taxes = self.calculate_total_with_taxes()

        # Calculate amount_due based on total_with_taxes
        self.amount_due = self.total_with_taxes - self.amount_paid

        super().save(*args, **kwargs)


class ReturnInvoiceDocument(models.Model):
    return_invoice = models.ForeignKey(ReturnInvoice, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=[
        ('Invoice', 'Invoice'),
    ])
    document = models.FileField(upload_to='return_invoice_documents/', null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    uploaded_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Worker who uploaded document", related_name='return_invoice_document'
    )

    def __str__(self):
        return f"{self.document_type} - {self.document.name}"


class ReturnInvoiceOrderItem(models.Model):
    return_invoice = models.ForeignKey(
        ReturnInvoice, related_name="items", on_delete=models.CASCADE
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    temp_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Price per unit of the product at the time of return"
    )

    def __str__(self):
        return f"Returned: {self.stock.product.product_code} - {self.stock.product.brand_name} (x{self.quantity})"

    def get_total_price(self):
        return self.temp_price * self.quantity


class ReturnItemTemp(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    invoice_order_item = models.ForeignKey(InvoiceOrderItem, on_delete=models.CASCADE)
    
    # Change from DecimalField to PositiveIntegerField
    quantity_returned = models.PositiveIntegerField(default=0)

    reason_for_return = models.CharField(max_length=200, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_order_item.stock.product.product_code} - {self.quantity_returned}"



class InvoicePayment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Deposit', 'Bank Deposit'),
        ('Check', 'Check'),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="invoice_payment",
        help_text="The invoice associated with this payment"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid in this transaction")
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, help_text="Mode of payment used")
    payment_date = models.DateTimeField(null=True)
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the invoice")

    # Store the related payment account based on the mode of payment
    momo_account = models.ForeignKey(
        MomoInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="momo_payments"
    )
    check_account = models.ForeignKey(
        Check, on_delete=models.SET_NULL, null=True, blank=True, related_name="check_payments"
    )
    bank_deposit_account = models.ForeignKey(
        BankDeposit, on_delete=models.SET_NULL, null=True, blank=True, related_name="deposit_payments"
    )

    def __str__(self):
        return f"Payment for Invoice #{self.invoice.id} - {self.payment_mode} ({self.amount_paid})"




class ReturnInvoicePayment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Bank Deposit', 'Bank Deposit'),
        ('Check', 'Check'),
    ]

    return_invoice = models.ForeignKey(
        ReturnInvoice,
        on_delete=models.CASCADE,
        related_name="return_invoice_payment",
        help_text="The return invoice associated with this payment"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid in this transaction")
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES, help_text="Mode of payment used")
    payment_date = models.DateTimeField(null=True)
    invoice_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount of the invoice")

    # Store the related payment account based on the mode of payment
    momo_account = models.ForeignKey(
        MomoInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_momo_payments"
    )
    check_account = models.ForeignKey(
        Check, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_check_payments"
    )
    bank_deposit_account = models.ForeignKey(
        BankDeposit, on_delete=models.SET_NULL, null=True, blank=True, related_name="return_deposit_payments"
    )

    def __str__(self):
        return f"Payment for Invoice #{self.invoice.id} - {self.payment_mode} ({self.amount_paid})"


class Receipt(models.Model):
    PAYMENT_METHODS = [
        ('Credit', 'Credit'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
    ]

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='receipts',
        help_text="Invoice associated with this receipt"
    )
    invoice_payment = models.ForeignKey(  # ✅ Allow multiple receipts for payments
        InvoicePayment, on_delete=models.SET_NULL, null=True, related_name='receipts'
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




class ReturnReceipt(models.Model):
    PAYMENT_METHODS = [
        ('Credit', 'Credit'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Mobile Money', 'Mobile Money'),
    ]

    return_invoice = models.ForeignKey(
        ReturnInvoice, on_delete=models.CASCADE, related_name='return_receipts',
        help_text="Return Invoice associated with this receipt"
    )
    return_invoice_payment = models.ForeignKey(
        ReturnInvoicePayment, on_delete=models.SET_NULL, null=True, related_name='receipts'
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
        if not self.return_invoice or not self.return_invoice.return_invoice_id:
            raise ValueError("An invoice must be associated with the receipt.")

        # Extract branch region from the invoice ID (Ensure correct format)
        try:
            reg = self.return_invoice.return_invoice_id.split('-')[1]
        except IndexError:
            raise ValueError("Invalid invoice ID format.")

        # Current date in YYYYMMDD format
        date_part = timezone.now().strftime("%Y%m%d")

        # Find the latest receipt for this branch (ignoring the date)
        last_receipt = ReturnReceipt.objects.filter(receipt_id__startswith=f"RET-RCT-{reg}-").order_by('-receipt_id').first()

        if last_receipt:
            # Extract and increment the last sequence number
            try:
                last_sequence = int(last_receipt.receipt_id.split('-')[-1])
                sequence = last_sequence + 1
            except ValueError:
                sequence = 1  # Fallback if sequence extraction fails
        else:
            sequence = 1  # Start sequence at 1 if no receipts exist

        # Generate the new receipt ID
        return f"RET-RCT-{reg}-{date_part}-{sequence:05d}"

    def save(self, *args, **kwargs):
        with transaction.atomic():  # Ensure atomicity to prevent race conditions
            if not self.receipt_id:
                self.receipt_id = self.generate_receipt_id()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_id} for Invoice {self.return_invoice.return_invoice_id}"



class ReturnOrderItem(models.Model):

    REASON_CHOICES = [
        ('Non-payment', 'Non-payment'),
        ('Damaged product', 'Damaged product'),
        ('Compromised packaging', 'Compromised packaging'),
        ('Incorrect quantity', 'Incorrect quantity'),
        ('Expiry date due', 'Expiry date due'),
        ('Incorrect item', 'Incorrect item'),
    ]

    invoice_order_item = models.ForeignKey(InvoiceOrderItem, on_delete=models.CASCADE)
    quantity_returned = models.PositiveIntegerField()
    reason_for_return = models.CharField(max_length=50, choices=REASON_CHOICES, null=True)
    return_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_order_items_created_by'
    )

    def __str__(self):
        return f"Return for {self.invoice_order_item.stock.product.product_code} (x{self.quantity_returned})"
