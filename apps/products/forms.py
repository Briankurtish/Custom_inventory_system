from django import forms
from .models import Batch, Product
from apps.genericName.models import GenericName

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'generic_name', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),  # Use date input for expiry date
        }
    
    # Change 'generic_name' to a ModelChoiceField to fetch data from GenericName table
    generic_name = forms.ModelChoiceField(
        queryset=GenericName.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the generic name from the list"
    )




class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        has_price_privilege = kwargs.pop('has_price_privilege', False)
        super().__init__(*args, **kwargs)

        if has_price_privilege:
            # Add the unit_price field dynamically
            self.fields['unit_price'] = forms.DecimalField(
                max_digits=10,
                decimal_places=2,
                required=True,
                widget=forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
                help_text="Unit Price of the product"
            )
            # Pre-populate with the instance value if available
            if self.instance and self.instance.pk:
                self.fields['unit_price'].initial = self.instance.unit_price

        # Debugging: Check if unit_price is in the form fields
        print("Fields in form:", self.fields.keys())



class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }


class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }



class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch', 'unit_price']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'unit_price': forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill the unit_price if the instance exists
        if self.instance and self.instance.pk:
            self.fields['unit_price'].initial = self.instance.unit_price
