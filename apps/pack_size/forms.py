from django import forms
from .models import PackSize
from django.utils.translation import gettext_lazy as _

class PackSizeForm(forms.ModelForm):
    class Meta:
        model = PackSize
        fields = ['pack_size']
        widgets = {
            'pack_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter Pack Size')}),
        }
        labels = {
            'pack_size': _('Pack Size'),
        }
