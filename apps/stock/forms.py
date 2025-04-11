from django import forms

from apps.branches.models import Branch
from apps.products.models import Batch, Product
from .models import Stock  # Import your Branch model

class StockAddForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('product', 'batch', 'branch', 'quantity')  # Added 'batch'

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        batch = cleaned_data.get('batch')

        # Optional: Validate that the batch matches the product's batch
        if product and batch and product.batch != batch:
            raise forms.ValidationError(
                "Selected batch {batch.batch_number} does not match product batch {product.batch.batch_number}."
            )
        return cleaned_data
    
    
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
    batch = forms.ModelChoiceField(queryset=Batch.objects.all(), required=True)  # Added batch field
    branch = forms.ModelChoiceField(queryset=Branch.objects.all())
    quantity = forms.IntegerField(min_value=0, label="Quantity")

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        batch = cleaned_data.get('batch')

        # Optional: Validate that the batch matches the product's batch
        if product and batch and product.batch != batch:
            raise forms.ValidationError(
                "Selected batch {batch.batch_number} does not match product batch {product.batch.batch_number}."
            )
        return cleaned_data


class UpdateStockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('product', 'quantity', 'branch')
