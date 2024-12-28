from django import forms
from .models import PurchaseOrder, PurchaseOrderItem
from apps.stock.models import Stock
from apps.branches.models import Branch
from apps.customers.models import Customer
from apps.workers.models import Worker


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['branch', 'customer', 'sales_rep', 'payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'branch': 'Branch',
            'customer': 'Customer',
            'sales_rep': 'Sales Representative',
            'payment_method': 'Payment Method',
        }

    def __init__(self, *args, **kwargs):
        user_branch = kwargs.pop('user_branch', None)
        super().__init__(*args, **kwargs)

        if user_branch:
            # Filter branches by the user's branch and set it as read-only
            self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            self.fields['branch'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
            
            # Filter sales reps based on the user's branch and role
            self.fields['sales_rep'].queryset = Worker.objects.filter(branch=user_branch, role="Sales Rep")


        # Set the customer queryset to all customers
        self.fields['customer'].queryset = Customer.objects.all()

        # Apply the form-control class to all fields for styling
        self.fields['branch'].widget.attrs.update({'class': 'form-control'})
        self.fields['customer'].widget.attrs.update({'class': 'form-control'})
        self.fields['sales_rep'].widget.attrs.update({'class': 'form-control'})



class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
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
            lambda obj: f"{obj.product.product_code} - {obj.product.generic_name_dosage} ({obj.quantity} available)"
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        stock = self.cleaned_data.get('stock')

        if stock and quantity > stock.quantity:
            raise forms.ValidationError(
                f"Insufficient stock: only {stock.quantity} units available for {stock.product.generic_name_dosage}."
            )
        return quantity