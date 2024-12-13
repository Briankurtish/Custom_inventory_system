from django import forms
from .models import BrandNameModel

class BrandForm(forms.ModelForm):
    class Meta:
        model = BrandNameModel
        fields = ['brand_name']
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Brand Name'}),
        }
        labels = {
            'brand_name': 'Brand Name',
        }
