from django import forms
from .models import PurchaseOrder, PurchaseOrderItem, InvoicePayment
from apps.stock.models import Stock
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker
from django.utils.translation import gettext_lazy as _


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['branch', 'customer', 'sales_rep', 'payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'branch': _('Branch'),
            'customer': _('Customer'),
            'sales_rep': _('Sales Representative'),
            'payment_method': _('Payment Method'),
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            if user_branch.is_superuser:
                # Superuser: Allow access to all branches and sales reps
                self.fields['branch'].queryset = Branch.objects.all()
                self.fields['sales_rep'].queryset = Worker.objects.filter(role="Sales Rep")
            else:
                # Regular users: Restrict to their branch
                self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
                self.fields['branch'].disabled = True  # Make the field immutable

                # Restrict sales reps to the user's branch
                self.fields['sales_rep'].queryset = Worker.objects.filter(branch=user_branch, role="Sales Rep")

        # Set customer queryset to all customers (modify if filtering is needed)
        self.fields['customer'].queryset = Customer.objects.all()

        # Apply consistent styling to all fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})



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
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Limit stock to the user's branch
            self.fields['stock'].queryset = Stock.objects.filter(branch=user_branch)
        self.fields['stock'].widget.attrs.update({'class': 'form-control'})
        self.fields['stock'].label_from_instance = (
            lambda obj: f"{obj.product.product_code} - {obj.product.generic_name_dosage} ({obj.quantity} available)"
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('stock')

        if stock and quantity > stock.quantity:
            raise forms.ValidationError(
                _(f"Insufficient stock: only {stock.quantity} units available for {stock.product.generic_name_dosage}.")
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







class InvoicePaymentForm(forms.ModelForm):
    class Meta:
        model = InvoicePayment
        fields = ['amount_paid', 'payment_mode', 'account_paid_to']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'account_paid_to': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'amount_paid': _('Amount Paid'),  # Translatable label
            'payment_mode': _('Payment Mode'),  # Translatable label
            'account_paid_to': _('Account Paid to'),  # Translatable label

        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)  # Pass the invoice instance to the form
        super().__init__(*args, **kwargs)

    def clean_amount_paid(self):
        """
        Validate that the amount paid does not exceed the amount due.
        """
        amount_paid = self.cleaned_data.get('amount_paid')

        if self.invoice:
            if amount_paid > self.invoice.amount_due:
                raise forms.ValidationError(f"Amount paid cannot exceed the remaining amount due ({self.invoice.amount_due}).")
            if amount_paid <= 0:
                raise forms.ValidationError(_("Amount paid must be greater than zero."))

        return amount_paid

    def save(self, commit=True):
        """
        Override save method to ensure the `invoice` field is set.
        """
        instance = super().save(commit=False)
        if self.invoice:
            instance.invoice = self.invoice
            instance.invoice_total = self.invoice.grand_total  # Set the invoice total on the payment instance
        if commit:
            instance.save()
        return instance
