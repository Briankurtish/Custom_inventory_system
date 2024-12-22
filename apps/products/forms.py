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
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'unit_price', 'batch']
        widgets = {
            'unit_price': forms.NumberInput(attrs={'type': 'number'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    # Ensure brand_name is populated with a GenericName instance
    brand_name = forms.ModelChoiceField(
        queryset=GenericName.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Brand name will be auto-filled based on the selected Generic Name."
    )

    # ModelChoiceField for selecting generic_name_dosage
    generic_name_dosage = forms.ModelChoiceField(
        queryset=GenericName.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the generic name dosage"
    )