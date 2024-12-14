from django import forms
from .models import Batch, Product

class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'generic_name', 'expiry_date']
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Generic name'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['brand_name', 'generic_name_dosage', 'pack_size', 'unit_price', 'batch']