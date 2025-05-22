from django import forms
from .models import Bank, BankDeposit, Check, InvoiceDocument, InvoiceOrderItem, MomoInfo, PaymentSchedule, PurchaseOrder, PurchaseOrderDocument, PurchaseOrderItem, InvoicePayment, ReturnInvoiceDocument, ReturnInvoiceOrderItem, ReturnInvoicePayment, ReturnOrderItem, ReturnPurchaseOrderDocument, ReturnPurchaseOrderItem, SampleOrderItem, Sickness, SicknessItem
from apps.stock.models import Stock
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from django.utils.translation import gettext_lazy as _


class PurchaseOrderForm(forms.ModelForm):
    ORDER_TYPE_CHOICES = [
        ('Purchase Order', 'Purchase Order'),
    ]

    order_type = forms.ChoiceField(
        choices=ORDER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    momo_account_details = forms.ModelChoiceField(
        queryset=MomoInfo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})  # Smaller input
    )
    check_account_details = forms.ModelChoiceField(
        queryset=Check.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})  # Smaller input
    )
    bank_deposit_account_details = forms.ModelChoiceField(
        queryset=BankDeposit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})  # Smaller input
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            'order_type', 'created_at', 'branch', 'customer', 'sales_rep', 'payment_method',
            'payment_mode', 'momo_account_details', 'check_account_details',
            'bank_deposit_account_details', 'tax_rate', 'precompte', 'tva', 'is_special_customer'
        ]
        widgets = {
            'created_at': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'customer': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'sales_rep': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_method': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tax_rate': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'precompte': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tva': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'is_special_customer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'created_at': 'Date',
            'branch': 'Branch',
            'customer': 'Customer',
            'sales_rep': 'Sales Representative',
            'payment_method': 'Payment Method',
            'payment_mode': 'Payment Mode',
            'tax_rate': 'Tax Rate',
            'precompte': 'Precompte',
            'tva': 'TVA',
            'is_special_customer': 'Special Customer',
        }

    def __init__(self, *args, **kwargs):
        user_is_superuser = kwargs.pop('user_is_superuser', False)
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)
        if not user_is_superuser and user_branch:
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['sales_rep'].queryset = Worker.objects.filter(branch=user_branch, role='Sales Rep')
            self.fields['customer'].queryset = Customer.objects.filter(branch=user_branch)
            self.fields['momo_account_details'].queryset = MomoInfo.objects.filter(branch=user_branch)
            self.fields['check_account_details'].queryset = Check.objects.filter(branch=user_branch)
            self.fields['bank_deposit_account_details'].queryset = BankDeposit.objects.filter(branch=user_branch)

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        payment_mode = cleaned_data.get('payment_mode')

        # Validate payment account details based on payment mode
        if payment_mode == 'Mobile Money':
            if not cleaned_data.get('momo_account_details'):
                raise forms.ValidationError('Mobile Money account details are required for Mobile Money payments.')
        elif payment_mode == 'Check':
            if not cleaned_data.get('check_account_details'):
                raise forms.ValidationError('Check account details are required for Check payments.')
        elif payment_mode == 'Bank Deposit':
            if not cleaned_data.get('bank_deposit_account_details'):
                raise forms.ValidationError('Bank deposit account details are required for Bank Deposit payments.')

        return cleaned_data

class SicknessOrderForm(forms.ModelForm):
    ORDER_TYPE_CHOICES = [
        ('Sickness', 'Sickness'),
    ]

    order_type = forms.ChoiceField(
        choices=ORDER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    momo_account_details = forms.ModelChoiceField(
        queryset=MomoInfo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    check_account_details = forms.ModelChoiceField(
        queryset=Check.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    bank_deposit_account_details = forms.ModelChoiceField(
        queryset=BankDeposit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    has_prescription = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_has_prescription'}),
        label=_('Has Prescription')
    )
    prescription_document = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_prescription_document'}),
        label=_('Prescription Document')
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            'order_type', 'created_at', 'branch', 'customer', 'employee', 'payment_method',
            'payment_mode', 'momo_account_details', 'check_account_details',
            'bank_deposit_account_details', 'tax_rate', 'precompte', 'tva', 'has_prescription', 'prescription_document'
        ]
        widgets = {
            'created_at': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'customer': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'employee': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_method': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tax_rate': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'precompte': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tva': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'has_prescription': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_has_prescription'}),
            'prescription_document': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_prescription_document'}),
        }
        labels = {
            'created_at': 'Date',
            'branch': 'Branch',
            'customer': 'Customer',
            'employee': 'Employee',
            'payment_method': 'Payment Method',
            'payment_mode': 'Payment Mode',
            'tax_rate': 'Tax Rate',
            'precompte': 'Precompte',
            'tva': 'TVA',
            'has_prescription': _('Has Prescription'),
            'prescription_document': _('Prescription Document'),
        }

    def __init__(self, *args, **kwargs):
        user_is_superuser = kwargs.pop('user_is_superuser', False)
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)
        if not user_is_superuser and user_branch:
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['employee'].queryset = Worker.objects.filter(branch=user_branch)
            self.fields['customer'].queryset = Customer.objects.filter(branch=user_branch)
            self.fields['momo_account_details'].queryset = MomoInfo.objects.filter(branch=user_branch)
            self.fields['check_account_details'].queryset = Check.objects.filter(branch=user_branch)
            self.fields['bank_deposit_account_details'].queryset = BankDeposit.objects.filter(branch=user_branch)

    def clean(self):
        cleaned_data = super().clean()
        payment_mode = cleaned_data.get('payment_mode')

        # Validate payment account details based on payment mode
        if payment_mode == 'Mobile Money':
            if not cleaned_data.get('momo_account_details'):
                raise forms.ValidationError('Mobile Money account details are required for Mobile Money payments.')
        elif payment_mode == 'Check':
            if not cleaned_data.get('check_account_details'):
                raise forms.ValidationError('Check account details are required for Check payments.')
        elif payment_mode == 'Bank Deposit':
            if not cleaned_data.get('bank_deposit_account_details'):
                raise forms.ValidationError('Bank deposit account details are required for Bank Deposit payments.')

        return cleaned_data


class SampleOrderForm(forms.ModelForm):
    ORDER_TYPE_CHOICES = [
        ('Sample', 'Sample'),
    ]

    order_type = forms.ChoiceField(
        choices=ORDER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    momo_account_details = forms.ModelChoiceField(
        queryset=MomoInfo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    check_account_details = forms.ModelChoiceField(
        queryset=Check.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    bank_deposit_account_details = forms.ModelChoiceField(
        queryset=BankDeposit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            'order_type', 'created_at', 'branch', 'customer', 'sales_rep', 'payment_method',
            'payment_mode', 'momo_account_details', 'check_account_details',
            'bank_deposit_account_details', 'tax_rate', 'precompte', 'tva'
        ]
        widgets = {
            'created_at': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'customer': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'sales_rep': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_method': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tax_rate': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'precompte': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'tva': forms.Select(attrs={'class': 'form-control form-control-sm'}),
        }
        labels = {
            'created_at': 'Date',
            'branch': 'Branch',
            'customer': 'Customer',
            'sales_rep': 'Sales Representative',
            'payment_method': 'Payment Method',
            'payment_mode': 'Payment Mode',
            'tax_rate': 'Tax Rate',
            'precompte': 'Precompte',
            'tva': 'TVA',
        }

    def __init__(self, *args, **kwargs):
        user_is_superuser = kwargs.pop('user_is_superuser', False)
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)
        if not user_is_superuser and user_branch:
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['sales_rep'].queryset = Worker.objects.filter(branch=user_branch, role='Sales Rep')
            self.fields['customer'].queryset = Customer.objects.filter(branch=user_branch)
            self.fields['momo_account_details'].queryset = MomoInfo.objects.filter(branch=user_branch)
            self.fields['check_account_details'].queryset = Check.objects.filter(branch=user_branch)
            self.fields['bank_deposit_account_details'].queryset = BankDeposit.objects.filter(branch=user_branch)

    def clean(self):
        cleaned_data = super().clean()
        payment_mode = cleaned_data.get('payment_mode')

        # Validate payment account details based on payment mode
        if payment_mode == 'Mobile Money':
            if not cleaned_data.get('momo_account_details'):
                raise forms.ValidationError('Mobile Money account details are required for Mobile Money payments.')
        elif payment_mode == 'Check':
            if not cleaned_data.get('check_account_details'):
                raise forms.ValidationError('Check account details are required for Check payments.')
        elif payment_mode == 'Bank Deposit':
            if not cleaned_data.get('bank_deposit_account_details'):
                raise forms.ValidationError('Bank deposit account details are required for Bank Deposit payments.')

        return cleaned_data






class PaymentScheduleForm(forms.ModelForm):
    class Meta:
        model = PaymentSchedule
        fields = ['when', 'amount', 'payment_date']  # Removed 'purchase_order'
        widgets = {
            'when': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }



class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['stock', 'quantity', 'temp_price', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'stock': _('Product'),
            'quantity': _('Quantity'),
            'temp_price': _('Price'),
            'reason': _("Note")
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user instance
        user_branch = kwargs.pop('user_branch', None)  # User's assigned branch
        selected_branch = kwargs.get('instance').branch if kwargs.get('instance') else None  # Branch from Purchase Order
        super().__init__(*args, **kwargs)

        # Determine which branch to use for filtering stock
        branch_to_filter = selected_branch if user and user.is_superuser else user_branch

        if branch_to_filter:
            self.fields['stock'].queryset = Stock.objects.filter(branch=branch_to_filter)

        self.fields['stock'].widget.attrs.update({'class': 'form-control'})
        self.fields['stock'].label_from_instance = (
            lambda obj: f"{obj.product.product_code} - {obj.product.generic_name_dosage} - {obj.product.brand_name.brand_name if obj.product.brand_name else ''} - {obj.product.batch.batch_number} ({obj.total_stock} available)"
        )


    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('stock')

        if stock and quantity > stock.total_stock:
            raise forms.ValidationError(
                _(f"Insufficient stock: only {stock.total_stock} units available for {stock.product.generic_name_dosage}.")
            )
        return quantity

    def clean_temp_price(self):
        temp_price = self.cleaned_data.get('temp_price')
        stock = self.cleaned_data.get('stock')

        if stock:
            stock_price = stock.product.unit_price
            if temp_price < stock_price:
                raise forms.ValidationError(
                    _(f"The entered price ({temp_price}) cannot be below the base price ({stock_price}).")
                )
        return temp_price





class SampleOrderItemForm(forms.ModelForm):
    class Meta:
        model = SampleOrderItem
        fields = ['stock', 'quantity', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'stock': _('Product'),
            'quantity': _('Quantity'),
            'reason': _("Note")
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user instance
        user_branch = kwargs.pop('user_branch', None)  # User's assigned branch
        selected_branch = kwargs.get('instance').branch if kwargs.get('instance') else None  # Branch from Purchase Order
        super().__init__(*args, **kwargs)

        # Determine which branch to use for filtering stock
        branch_to_filter = selected_branch if user and user.is_superuser else user_branch

        if branch_to_filter:
            self.fields['stock'].queryset = Stock.objects.filter(branch=branch_to_filter)

        self.fields['stock'].widget.attrs.update({'class': 'form-control'})
        self.fields['stock'].label_from_instance = (
            lambda obj: f"{obj.product.product_code} - {obj.product.generic_name_dosage} - {obj.product.brand_name.brand_name if obj.product.brand_name else ''} - {obj.product.batch.batch_number} ({obj.total_stock} available)"
        )


    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('stock')

        if stock and quantity > stock.total_stock:
            raise forms.ValidationError(
                _(f"Insufficient stock: only {stock.total_stock} units available for {stock.product.generic_name_dosage}.")
            )
        return quantity






class InvoicePaymentForm(forms.ModelForm):
    momo_account = forms.ModelChoiceField(
        queryset=MomoInfo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )
    check_account = forms.ModelChoiceField(
        queryset=Check.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )
    bank_deposit_account = forms.ModelChoiceField(
        queryset=BankDeposit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )

    class Meta:
        model = InvoicePayment
        fields = ['payment_date','amount_paid', 'payment_mode', 'momo_account', 'check_account', 'bank_deposit_account']
        widgets = {
            'payment_date': forms.DateTimeInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'payment_mode': forms.Select(attrs={'class': 'form-control', 'id': 'payment_mode'}),
        }
        labels = {
            'momo_account': '',
            'check_account': '',
            'bank_deposit_account': '',
        }

    def __init__(self, *args, **kwargs):
        """Pass invoice instance and dynamically adjust field visibility."""
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Ensure only the relevant account field is stored based on payment mode.
        """
        instance = super().save(commit=False)

        # Reset all account fields
        instance.momo_account = None
        instance.check_account = None
        instance.bank_deposit_account = None

        # Assign the correct account field
        if instance.payment_mode == "Mobile Money":
            instance.momo_account = self.cleaned_data.get('momo_account')
        elif instance.payment_mode == "Check":
            instance.check_account = self.cleaned_data.get('check_account')
        elif instance.payment_mode == "Bank Deposit":
            instance.bank_deposit_account = self.cleaned_data.get('bank_deposit_account')

        if commit:
            instance.save()
        return instance



class ReturnInvoicePaymentForm(forms.ModelForm):
    momo_account = forms.ModelChoiceField(
        queryset=MomoInfo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )
    check_account = forms.ModelChoiceField(
        queryset=Check.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )
    bank_deposit_account = forms.ModelChoiceField(
        queryset=BankDeposit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control hidden-field'})  # Initially hidden
    )

    class Meta:
        model = ReturnInvoicePayment
        fields = ['payment_date','amount_paid', 'payment_mode', 'momo_account', 'check_account', 'bank_deposit_account']
        widgets = {
            'payment_date': forms.DateTimeInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'payment_mode': forms.Select(attrs={'class': 'form-control', 'id': 'payment_mode'}),
        }
        labels = {
            'momo_account': '',
            'check_account': '',
            'bank_deposit_account': '',
        }

    def __init__(self, *args, **kwargs):
        """Pass invoice instance and dynamically adjust field visibility."""
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """
        Ensure only the relevant account field is stored based on payment mode.
        """
        instance = super().save(commit=False)

        # Reset all account fields
        instance.momo_account = None
        instance.check_account = None
        instance.bank_deposit_account = None

        # Assign the correct account field
        if instance.payment_mode == "Mobile Money":
            instance.momo_account = self.cleaned_data.get('momo_account')
        elif instance.payment_mode == "Check":
            instance.check_account = self.cleaned_data.get('check_account')
        elif instance.payment_mode == "Bank Deposit":
            instance.bank_deposit_account = self.cleaned_data.get('bank_deposit_account')

        if commit:
            instance.save()
        return instance



class BankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ['name', 'account_name', 'bank_code', 'code_agency', 'account_number', 'rib']

class MomoInfoForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = MomoInfo
        fields = ['branch', 'master_sim_name', 'master_sim_no', 'momo_number', 'momo_name', 'payment_type', 'bank']

    def __init__(self, *args, **kwargs):
        super(MomoInfoForm, self).__init__(*args, **kwargs)

        # Hide the payment_type field and set its initial value
        self.fields['payment_type'].widget = forms.HiddenInput()
        self.fields['payment_type'].initial = "Mobile Money"


class CheckForm(forms.ModelForm):
    class Meta:
        model = Check
        fields = ['branch', 'bank', 'payment_type']

    def __init__(self, *args, **kwargs):
        super(CheckForm, self).__init__(*args, **kwargs)

        # Hide the payment_type field and set its initial value
        self.fields['payment_type'].widget = forms.HiddenInput()
        self.fields['payment_type'].initial = "Check"



class BankDepositForm(forms.ModelForm):
    class Meta:
        model = BankDeposit
        fields = ['branch', 'bank', 'payment_type']

    def __init__(self, *args, **kwargs):
        super(BankDepositForm, self).__init__(*args, **kwargs)

        # Hide the payment_type field and set its initial value
        self.fields['payment_type'].widget = forms.HiddenInput()
        self.fields['payment_type'].initial = "Bank Deposit"


class ReturnOrderItemForm(forms.Form):
    RETURN_REASONS = [
        ('Non-payment', 'Non-payment'),
        ('Damaged product', 'Damaged product'),
        ('Compromised packaging', 'Compromised packaging'),
        ('Incorrect quantity', 'Incorrect quantity'),
        ('Expiry date due', 'Expiry date due'),
        ('Incorrect item', 'Incorrect item'),
        ('other', 'Other')
    ]
    return_date = forms.DateTimeField(
        label="Return Date",
        widget=forms.DateTimeInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    invoice_order_item = forms.ModelChoiceField(
        queryset=InvoiceOrderItem.objects.none(),
        label="Item to Return",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity_returned = forms.IntegerField(
        label="Quantity to Return",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    reason_for_return = forms.ChoiceField(
        label="Reason for Return",
        choices=RETURN_REASONS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, invoice_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if invoice_id:
            self.fields['invoice_order_item'].queryset = InvoiceOrderItem.objects.filter(
                invoice_order__id=invoice_id
            )

    def clean_quantity_returned(self):
        quantity = self.cleaned_data.get('quantity_returned')
        invoice_order_item = self.cleaned_data.get('invoice_order_item')

        if invoice_order_item and quantity > invoice_order_item.quantity:
            raise forms.ValidationError(
                f"Cannot return more than {invoice_order_item.quantity} items."
            )
        return quantity







class PurchaseOrderTaxForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['tax_rate', 'precompte', 'tva']
        widgets = {
            'tax_rate': forms.Select(attrs={'class': 'form-control'}),
            'precompte': forms.Select(attrs={'class': 'form-control'}),
            'tva': forms.Select(attrs={'class': 'form-control'}),
        }


# class PurchaseOrderDocumentForm(forms.ModelForm):
#     DOCUMENT_TYPE_CHOICES = [
#         ('Purchase Order', 'Purchase Order'),
#         ('Invoice', 'Invoice'),
#     ]

#     document_type = forms.ChoiceField(choices=DOCUMENT_TYPE_CHOICES, label="Document Type")
#     document = forms.FileField(label="Upload Document")

#     class Meta:
#         model = PurchaseOrder
#         fields = ['document_type', 'document']



class PurchaseOrderDocumentForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderDocument
        fields = ['document_type', 'document']


class ReturnPurchaseOrderDocumentForm(forms.ModelForm):
    class Meta:
        model = ReturnPurchaseOrderDocument
        fields = ['document_type', 'document']


class InvoicerDocumentForm(forms.ModelForm):
    class Meta:
        model = InvoiceDocument
        fields = ['document_type', 'document']

class ReturnInvoiceDocumentForm(forms.ModelForm):
    class Meta:
        model = ReturnInvoiceDocument
        fields = ['document_type', 'document']

class SicknessForm(forms.ModelForm):
    class Meta:
        model = Sickness
        fields = ['branch', 'employee', 'has_prescription']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'has_prescription': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Worker.objects.all().order_by("user__first_name")
        self.fields['branch'].queryset = Branch.objects.all()


class SicknessItemForm(forms.ModelForm):
    class Meta:
        model = SicknessItem
        fields = ['stock', 'quantity', 'reason']
        widgets = {
            'stock': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)
        if user_branch:
            self.fields['stock'].queryset = Stock.objects.filter(branch=user_branch, quantity__gt=0)
        else:
            self.fields['stock'].queryset = Stock.objects.filter(quantity__gt=0)
        self.fields['stock'].label_from_instance = (
            lambda obj: f"{obj.product.product_code} - {obj.product.generic_name_dosage} - {obj.product.brand_name.brand_name if obj.product.brand_name else ''} - {obj.product.batch.batch_number} ({obj.total_stock} available)"
        )
