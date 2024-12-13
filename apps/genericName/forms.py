from django import forms
from .models import GenericName

class BrandForm(forms.ModelForm):
    class Meta:
        model = GenericName
        fields = ['generic_name']
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Generic Name'}),
        }
        labels = {
            'generic_name': 'Generic Name',
        }
