from datetime import datetime
from django import forms
from apps.oldinvoice.models import OldInvoiceOrder, OldInvoiceOrderItem
from apps.stock.models import Stock
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker


from django import forms
from .models import OldInvoiceOrder


class OldInvoiceOrderForm(forms.ModelForm):
    class Meta:
        model = OldInvoiceOrder
        fields = ['branch', 'customer', 'sales_rep', 'payment_method', 'amount_paid', 'created_at']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'created_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'branch': 'Branch',
            'customer': 'Customer',
            'sales_rep': 'Sales Representative',
            'payment_method': 'Payment Method',
            'amount_paid': 'Amount Paid',
            'created_at': 'Invoice Date',
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Filter branches by the user's branch
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['branch'].widget.attrs.update({
                'class': 'form-control',
                'readonly': False,
                'disabled': False,
            })

            # Filter sales reps based on the user's branch
            self.fields['sales_rep'].queryset = Worker.objects.filter(branch=user_branch, role="Sales Rep")

        # Set the customer queryset to all customers
        self.fields['customer'].queryset = Customer.objects.all()

        # Apply the form-control class to all fields for styling
        for field in self.fields:
            if field not in ['payment_method', 'created_at', 'due_date']:  # Already styled
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get('amount_paid')
        grand_total = self.instance.grand_total  # Use instance if editing an existing order
        if amount_paid and grand_total and amount_paid > grand_total:
            raise forms.ValidationError("Amount paid cannot exceed the grand total.")
        return amount_paid




class OldInvoiceOrderItemForm(forms.ModelForm):
    class Meta:
        model = OldInvoiceOrderItem
        fields = ['stock', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'stock': 'Product',
            'quantity': 'Quantity',
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Limit stock to the user's branch
            self.fields['stock'].queryset = Stock.objects.filter(branch=user_branch)
        self.fields['stock'].widget.attrs.update({'class': 'form-control'})
        self.fields['stock'].label_from_instance = (
            lambda obj: f"{obj.product.product_code} - {obj.product.brand_name} ({obj.quantity} available)"
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('stock')

        
        return quantity
