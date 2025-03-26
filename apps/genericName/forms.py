from django import forms
from .models import GenericName
from django.utils.translation import gettext_lazy as _

class GenericNameForm(forms.ModelForm):
    class Meta:
        model = GenericName
        fields = ['generic_name', 'brand_name', 'old_brand_name']
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter Generic Name')}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter Brand Name (optional)')}),
            'old_brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter Old Brand Name (optional)')}),
        }
        labels = {
            'generic_name': _('Generic Name'),
            'brand_name': _('Brand Name'),
            'old_brand_name': _('Old Brand Name'),
        }
