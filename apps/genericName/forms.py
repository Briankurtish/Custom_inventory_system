from django import forms
from .models import GenericName

class GenericNameForm(forms.ModelForm):
    class Meta:
        model = GenericName
        fields = ['generic_name', 'brand_name']
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Generic Name'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Brand Name (optional)'}),
        }
        labels = {
            'generic_name': 'Generic Name',
            'brand_name': 'Brand Name (Optional)',
        }