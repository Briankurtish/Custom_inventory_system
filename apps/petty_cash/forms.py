from django import forms
from decimal import Decimal
from .models import (
    PettyCashCategory,
    PettyCashTransaction,
    PettyCashSettings,
    PettyCashRefillRequest,
    PettyCashReceipt
)
from apps.branches.models import Branch


class PettyCashTransactionForm(forms.ModelForm):
    """Form for creating/editing petty cash transactions"""

    class Meta:
        model = PettyCashTransaction
        fields = [
            'branch', 'channel', 'category', 'amount',
            'description', 'recipient', 'recipient_name', 'recipient_phone', 'override_reason'
        ]
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recipient': forms.Select(attrs={'class': 'form-select select2'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional: for external recipients'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'override_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Required if exceeding daily limit'}),
        }
        labels = {
            'recipient': 'Employee Recipient',
            'recipient_name': 'External Recipient Name (Optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only active branches
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)
        # Filter to show only active categories
        from apps.petty_cash.models import PettyCashCategory
        self.fields['category'].queryset = PettyCashCategory.objects.filter(is_active=True).order_by('name')
        # Filter to show only active employees, ordered by name
        from apps.workers.models import Worker
        self.fields['recipient'].queryset = Worker.objects.filter(is_active=True).select_related('user').order_by('user__first_name', 'user__last_name')
        self.fields['recipient'].required = False
        self.fields['recipient_name'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Always set transaction type to Disbursement
        instance.transaction_type = 'Disbursement'
        if commit:
            instance.save()
        return instance


class PettyCashApprovalForm(forms.Form):
    """Form for approving/rejecting transactions"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Required if rejecting'}),
        label="Rejection Reason"
    )
    override_approval = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Approve Override (for transactions exceeding limits)"
    )


class PettyCashSettingsForm(forms.ModelForm):
    """Form for updating petty cash settings"""

    class Meta:
        model = PettyCashSettings
        fields = [
            'daily_cash_limit', 'daily_momo_limit', 'daily_orange_limit',
            'cash_refill_threshold', 'momo_refill_threshold', 'orange_refill_threshold',
            'receipt_required_threshold', 'requires_override_approval'
        ]
        widgets = {
            'daily_cash_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'daily_momo_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'daily_orange_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'cash_refill_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'momo_refill_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'orange_refill_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'receipt_required_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'requires_override_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'daily_cash_limit': 'Daily Cash Limit (CFA)',
            'daily_momo_limit': 'Daily MTN MoMo Limit (CFA)',
            'daily_orange_limit': 'Daily Orange Money Limit (CFA)',
            'cash_refill_threshold': 'Cash Refill Alert Threshold (CFA)',
            'momo_refill_threshold': 'MoMo Refill Alert Threshold (CFA)',
            'orange_refill_threshold': 'Orange Money Refill Alert Threshold (CFA)',
            'receipt_required_threshold': 'Receipt Required Above (CFA)',
            'requires_override_approval': 'Require Manager Approval for Limit Overrides',
        }


class PettyCashRefillRequestForm(forms.ModelForm):
    """Form for requesting petty cash refill with flexible channel distribution"""

    class Meta:
        model = PettyCashRefillRequest
        fields = ['branch', 'source_type', 'source_branch', 'requested_amount', 'justification']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'source_branch': forms.Select(attrs={'class': 'form-select'}),
            'requested_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'justification': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain why this refill is needed'}),
        }
        labels = {
            'branch': 'Requesting Branch',
            'source_type': 'Source of Funds',
            'source_branch': 'Source Branch (for transfers)',
            'requested_amount': 'Total Amount Requested (CFA)',
            'justification': 'Justification',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only active branches
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True)
        self.fields['source_branch'].queryset = Branch.objects.filter(is_active=True)
        self.fields['source_branch'].required = False

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type')
        source_branch = cleaned_data.get('source_branch')
        requesting_branch = cleaned_data.get('branch')

        # Validate source branch is required for branch transfers
        if source_type == 'Branch Transfer' and not source_branch:
            self.add_error('source_branch', 'Please select a source branch for branch transfers')

        # Validate source and destination branches are different
        if source_type == 'Branch Transfer' and source_branch and requesting_branch:
            if source_branch.id == requesting_branch.id:
                self.add_error('source_branch', 'Source and destination branches must be different')

        return cleaned_data


class PettyCashRefillApprovalForm(forms.Form):
    """Form for approving/rejecting refill requests"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject'), ('complete', 'Mark as Completed')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Required if rejecting'}),
        label="Rejection Reason"
    )


class PettyCashRefillCompletionForm(forms.Form):
    """Form for completing refill with channel distribution"""
    cash_amount = forms.DecimalField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Cash Amount (CFA)"
    )
    momo_amount = forms.DecimalField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="MTN MoMo Amount (CFA)"
    )
    orange_amount = forms.DecimalField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Orange Money Amount (CFA)"
    )

    def __init__(self, *args, **kwargs):
        self.requested_amount = kwargs.pop('requested_amount', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cash = cleaned_data.get('cash_amount') or Decimal('0')
        momo = cleaned_data.get('momo_amount') or Decimal('0')
        orange = cleaned_data.get('orange_amount') or Decimal('0')

        total = cash + momo + orange

        # Validate total matches requested amount
        if self.requested_amount and total != self.requested_amount:
            raise forms.ValidationError(
                f"Total distribution ({total} CFA) must equal requested amount ({self.requested_amount} CFA)"
            )

        # At least one channel must have amount
        if total == 0:
            raise forms.ValidationError("At least one channel must have an amount greater than 0")

        return cleaned_data


class PettyCashReceiptForm(forms.ModelForm):
    """Form for uploading receipts"""

    class Meta:
        model = PettyCashReceipt
        fields = ['receipt_file', 'notes']
        widgets = {
            'receipt_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PettyCashReportFilterForm(forms.Form):
    """Form for filtering reports"""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Start Date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="End Date"
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=False,
        empty_label="All Branches",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Branch"
    )
    channel = forms.ChoiceField(
        choices=[('', 'All Channels'), ('Cash', 'Cash'), ('MTN MoMo', 'MTN MoMo'), ('Orange Money', 'Orange Money')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Payment Channel"
    )
    category = forms.ModelChoiceField(
        queryset=PettyCashCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Category"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(PettyCashTransaction.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Status"
    )
