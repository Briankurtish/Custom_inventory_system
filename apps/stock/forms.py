from django import forms

from apps.branches.models import Branch
from apps.products.models import Batch, Product
from .models import Stock  # Import your Branch model
from .models import Supplier

class StockAddForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False, label="Supplier")
    class Meta:
        model = Stock
        fields = ('product', 'batch', 'branch', 'quantity', 'supplier')

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
        queryset=Branch.objects.filter(is_active=True),
        label="Branch",
        required=True
    )
    fixed_beginning_inventory = forms.IntegerField(
        min_value=0,
        label="Beginning Inventory",
        required=True
    )


class StockUpdateForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product"
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        required=True,
        label="Batch Number"
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        label="Branch"
    )
    quantity = forms.IntegerField(
        min_value=0,
        label="Quantity"
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        label="Supplier"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter products based on existing stock for the selected branch and batch
        if 'branch' in self.data:
            branch_id = self.data.get('branch')
            if branch_id:
                self.fields['product'].queryset = Product.objects.filter(
                    stocks__branch_id=branch_id  # Use 'stocks' as the reverse relation
                ).distinct()
        if 'batch' in self.data:
            batch_id = self.data.get('batch')
            if batch_id:
                self.fields['product'].queryset = self.fields['product'].queryset.filter(
                    stocks__batch_id=batch_id  # Use 'stocks' as the reverse relation
                ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        batch = cleaned_data.get('batch')
        branch = cleaned_data.get('branch')

        if product and batch and branch:
            # Verify stock record exists
            if not Stock.objects.filter(product=product, batch=batch, branch=branch).exists():
                raise forms.ValidationError(
                    f"No stock record found for {product.generic_name_dosage.generic_name} (Batch: {batch.batch_number}) "
                    f"in branch {branch.branch_name}. Please select a valid product or create a new stock record."
                )
        return cleaned_data


class UpdateStockForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False, label="Supplier")
    class Meta:
        model = Stock
        fields = ('product', 'quantity', 'branch', 'supplier')


class EditStockDetailsForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False, label="Supplier")
    class Meta:
        model = Stock
        exclude = ('quantity', 'total_inventory', 'begining_inventory', 'fixed_beginning_inventory', 'quantity_transferred', 'return_quantity', 'damaged_quantity', 'samples_quantity', 'sickness_quantity', 'total_sold', 'total_stock', 'created_by', 'date_added')


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'address']
