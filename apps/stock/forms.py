from django import forms

from apps.branches.models import Branch
from apps.products.models import Product
from .models import Stock  # Import your Branch model

class StockAddForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('product', 'branch', 'quantity')

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

class BeginningInventoryForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        required=True
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Branch",
        required=True
    )
    fixed_beginning_inventory = forms.IntegerField(
        min_value=0,
        label="Beginning Inventory",
        required=True
    )


class StockUpdateForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    branch = forms.ModelChoiceField(queryset=Branch.objects.all())
    quantity = forms.IntegerField(min_value=0, label="Quantity")


class UpdateStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('product', 'quantity', 'branch')
