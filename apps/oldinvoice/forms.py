from datetime import datetime
from django import forms
from apps.oldinvoice.models import OldInvoiceOrder, OldInvoiceOrderItem, InvoicePaymentHistory
from apps.orders.models import BankDeposit, Check, MomoInfo
from apps.products.models import Product
from apps.stock.models import Stock
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from django import forms
from .models import OldInvoiceOrder


class OldInvoiceOrderForm(forms.ModelForm):
    class Meta:
        model = OldInvoiceOrder
        fields = ['old_invoice_id','branch', 'customer', 'sales_rep', 'payment_method', 'created_at']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            # 'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'created_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'old_invoice_id': _('Old Invoice ID'),
            'branch': _('Branch'),
            'customer': _('Customer'),
            'sales_rep': _('Sales Representative'),
            'payment_method': _('Payment Method'),
            # 'amount_paid': _('Amount Paid'),
            'created_at': _('Invoice Date'),
        }

    def __init__(self, *args, **kwargs):
        user_is_superuser = kwargs.pop('user_is_superuser', False)
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Regular user: Restrict to their branch
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['branch'].disabled = False  # Make the field immutable
            self.fields['sales_rep'].queryset = Worker.objects.all()
            self.fields['customer'].queryset = Customer.objects.filter(branch=user_branch)

        # Filter sales reps based on the user's branch
        self.fields['sales_rep'].queryset = Worker.objects.all()
        self.fields['branch'].queryset = Branch.objects.all()
        # Set the customer queryset to all customers
        self.fields['customer'].queryset = Customer.objects.all()

        # Apply the form-control class to all fields for styling
        for field in self.fields:
            if field not in ['payment_method', 'created_at', 'due_date']:  # Already styled
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    # def clean_amount_paid(self):
    #     amount_paid = self.cleaned_data.get('amount_paid')
    #     grand_total = self.instance.grand_total  # Use instance if editing an existing order
    #     if amount_paid and grand_total and amount_paid > grand_total:
    #         raise forms.ValidationError(_("Amount paid cannot exceed the grand total."))
    #     return amount_paid




class OldInvoiceOrderItemForm(forms.ModelForm):
    class Meta:
        model = OldInvoiceOrderItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'product': _('Product'),
            'quantity': _('Quantity'),
            'price': _('Price'),
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Limit stock to the user's branch
            self.fields['product'].queryset = Product.objects.all()
        self.fields['product'].widget.attrs.update({'class': 'form-control'})
        self.fields['product'].label_from_instance = (
            lambda obj: f"{obj.product_code} - {obj.brand_name.brand_name if obj.brand_name else 'No Brand'} -- ({obj.generic_name_dosage}) -- ({obj.dosage_type.name if obj.dosage_type else 'No Dosage Type'})"
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')


        return quantity


class InvoicePaymentHistoryForm(forms.ModelForm):
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
        model = InvoicePaymentHistory  # Assuming this model is related to payments
        fields = ['payment_date', 'amount_paid', 'payment_mode', 'momo_account', 'check_account', 'bank_deposit_account']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount paid'}),
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

        # Assign the correct account field based on payment mode
        if instance.payment_mode == "Mobile Money":
            instance.momo_account = self.cleaned_data.get('momo_account')
        elif instance.payment_mode == "Check":
            instance.check_account = self.cleaned_data.get('check_account')
        elif instance.payment_mode == "Bank Deposit":
            instance.bank_deposit_account = self.cleaned_data.get('bank_deposit_account')

        if commit:
            instance.save()
        return instance

    # account_paid_to_type = forms.ModelChoiceField(
    #     queryset=ContentType.objects.filter(
    #         model__in=['momoinfo', 'check', 'bankdeposit']
    #     ),
    #     required=True,
    #     widget=forms.Select(attrs={'placeholder': 'Select account type'}),
    # )
