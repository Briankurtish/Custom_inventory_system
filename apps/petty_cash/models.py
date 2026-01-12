from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.branches.models import Branch
from apps.workers.models import Worker


class PettyCashSettings(models.Model):
    """Global settings for petty cash management"""
    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, related_name='petty_cash_settings')

    # Daily limits per channel
    daily_cash_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'),
                                          help_text="Daily limit for cash disbursements")
    daily_momo_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'),
                                          help_text="Daily limit for MTN MoMo disbursements")
    daily_orange_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('50000.00'),
                                            help_text="Daily limit for Orange Money disbursements")

    # Refill thresholds
    cash_refill_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'),
                                               help_text="Alert when cash balance falls below this amount")
    momo_refill_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'),
                                               help_text="Alert when MoMo balance falls below this amount")
    orange_refill_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'),
                                                 help_text="Alert when Orange balance falls below this amount")

    # Receipt requirement threshold
    receipt_required_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'),
                                                    help_text="Receipts mandatory for amounts above this")

    # Override settings
    requires_override_approval = models.BooleanField(default=True, help_text="Require approval for limit overrides")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Petty Cash Settings"
        verbose_name_plural = "Petty Cash Settings"
        ordering = ['branch']

    def __str__(self):
        return f"Settings - {self.branch.branch_name}"


class PettyCashBalance(models.Model):
    """Track current balance per branch and payment channel"""
    CHANNEL_CHOICES = [
        ('Cash', 'Cash'),
        ('MTN MoMo', 'MTN MoMo'),
        ('Orange Money', 'Orange Money'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='petty_cash_balances')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    month = models.DateField(help_text="First day of the month")

    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_inflow = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_outflow = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Petty Cash Balance"
        verbose_name_plural = "Petty Cash Balances"
        unique_together = ['branch', 'channel', 'month']
        ordering = ['-month', 'branch', 'channel']

    def __str__(self):
        return f"{self.branch.branch_name} - {self.channel} - {self.month.strftime('%B %Y')}"


class PettyCashCategory(models.Model):
    """Categories for petty cash transactions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, related_name='created_petty_cash_categories')

    class Meta:
        verbose_name_plural = "Petty Cash Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class PettyCashTransaction(models.Model):
    """Main transaction record for petty cash"""
    TRANSACTION_TYPE_CHOICES = [
        ('Disbursement', 'Disbursement'),
        ('Refill', 'Refill'),
        ('Adjustment', 'Adjustment'),
    ]

    CHANNEL_CHOICES = [
        ('Cash', 'Cash'),
        ('MTN MoMo', 'MTN MoMo'),
        ('Orange Money', 'Orange Money'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Disbursed', 'Disbursed'),
        ('Cancelled', 'Cancelled'),
    ]

    transaction_id = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='petty_cash_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='Disbursement')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)

    category = models.ForeignKey(PettyCashCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(help_text="Purpose of transaction")

    # Recipient can be either an employee or external person
    recipient = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_receipts', help_text="Employee receiving the cash")
    recipient_name = models.CharField(max_length=200, null=True, blank=True, help_text="Person/entity receiving the cash (if not an employee)")
    recipient_phone = models.CharField(max_length=20, null=True, blank=True)

    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requires_override = models.BooleanField(default=False, help_text="Exceeds daily limit")
    override_approved = models.BooleanField(default=False)
    override_reason = models.TextField(null=True, blank=True)

    # Audit fields
    requested_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, related_name='petty_cash_requests')
    requested_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_approvals')
    approved_at = models.DateTimeField(null=True, blank=True)

    disbursed_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_disbursements')
    disbursed_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Petty Cash Transaction"
        verbose_name_plural = "Petty Cash Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['branch', 'channel', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['transaction_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate unique transaction ID: PC-BRANCH-YYYYMMDD-XXXXX
            today = timezone.now()
            date_part = today.strftime("%Y%m%d")
            branch_code = self.branch.branch_id.split("-")[0] if self.branch.branch_id else "UNK"

            base_prefix = f"PC-{branch_code}-{date_part}-"

            # Get the last transaction ID for today
            existing_ids = PettyCashTransaction.objects.filter(
                transaction_id__startswith=base_prefix
            ).values_list('transaction_id', flat=True)

            sequences = []
            for tid in existing_ids:
                try:
                    seq = int(tid.split('-')[-1])
                    sequences.append(seq)
                except (ValueError, IndexError):
                    continue

            next_sequence = max(sequences) + 1 if sequences else 1
            self.transaction_id = f"{base_prefix}{next_sequence:05d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - {self.recipient_name} - {self.amount} CFA"


class PettyCashReceipt(models.Model):
    """Receipt attachments for transactions"""
    transaction = models.ForeignKey(PettyCashTransaction, on_delete=models.CASCADE, related_name='receipts')
    receipt_file = models.FileField(upload_to='petty_cash_receipts/%Y/%m/', help_text="Upload receipt image/PDF")
    uploaded_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Petty Cash Receipt"
        verbose_name_plural = "Petty Cash Receipts"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Receipt for {self.transaction.transaction_id}"


class PettyCashRefillRequest(models.Model):
    """Requests for petty cash replenishment with multi-channel distribution"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    SOURCE_TYPE_CHOICES = [
        ('Central Finance', 'Central Finance'),
        ('Branch Transfer', 'Branch Transfer'),
    ]

    refill_id = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='petty_cash_refill_requests', help_text="Branch requesting refill")

    # Source of funds
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='Central Finance', help_text="Where funds will come from")
    source_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_refills', help_text="Source branch for transfers")

    # Request details
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total amount requested")
    justification = models.TextField(help_text="Reason for requesting refill")

    # Channel distribution (filled during completion)
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount disbursed as Cash")
    momo_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount disbursed as MTN MoMo")
    orange_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount disbursed as Orange Money")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    requested_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, related_name='petty_cash_refill_requests')
    requested_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_refill_approvals')
    approved_at = models.DateTimeField(null=True, blank=True)

    completed_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='petty_cash_refill_completions')
    completed_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Petty Cash Refill Request"
        verbose_name_plural = "Petty Cash Refill Requests"
        ordering = ['-requested_at']

    def save(self, *args, **kwargs):
        if not self.refill_id:
            # Generate unique refill ID: PCR-BRANCH-YYYYMMDD-XXX
            today = timezone.now()
            date_part = today.strftime("%Y%m%d")
            branch_code = self.branch.branch_id.split("-")[0] if self.branch.branch_id else "UNK"

            base_prefix = f"PCR-{branch_code}-{date_part}-"

            existing_ids = PettyCashRefillRequest.objects.filter(
                refill_id__startswith=base_prefix
            ).values_list('refill_id', flat=True)

            sequences = []
            for rid in existing_ids:
                try:
                    seq = int(rid.split('-')[-1])
                    sequences.append(seq)
                except (ValueError, IndexError):
                    continue

            next_sequence = max(sequences) + 1 if sequences else 1
            self.refill_id = f"{base_prefix}{next_sequence:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        source = f"from {self.source_branch.branch_name}" if self.source_type == 'Branch Transfer' and self.source_branch else "Central Finance"
        return f"{self.refill_id} - {self.branch.branch_name} ({source})"


class PettyCashAuditLog(models.Model):
    """Comprehensive audit trail for all petty cash activities"""
    ACTION_CHOICES = [
        ('Create Transaction', 'Create Transaction'),
        ('Approve Transaction', 'Approve Transaction'),
        ('Reject Transaction', 'Reject Transaction'),
        ('Disburse Transaction', 'Disburse Transaction'),
        ('Cancel Transaction', 'Cancel Transaction'),
        ('Override Approval', 'Override Approval'),
        ('Create Refill Request', 'Create Refill Request'),
        ('Edit Refill Request', 'Edit Refill Request'),
        ('Delete Refill Request', 'Delete Refill Request'),
        ('Approve Refill', 'Approve Refill'),
        ('Reject Refill', 'Reject Refill'),
        ('Complete Refill', 'Complete Refill'),
        ('Update Settings', 'Update Settings'),
        ('Upload Receipt', 'Upload Receipt'),
        ('Balance Adjustment', 'Balance Adjustment'),
    ]

    user = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, related_name='petty_cash_audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    transaction = models.ForeignKey(PettyCashTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    refill_request = models.ForeignKey(PettyCashRefillRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    details = models.TextField(help_text="Description of the action performed")
    timestamp = models.DateTimeField(auto_now_add=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Petty Cash Audit Log"
        verbose_name_plural = "Petty Cash Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'action']),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
