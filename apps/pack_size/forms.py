from django import forms
from .models import PackSize

class PackSizeForm(forms.ModelForm):
    class Meta:
        model = PackSize
        fields = ['pack_size']
        widgets = {
            'pack_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Pack Size'}),
        }
        labels = {
            'pack_size': 'Pack Size',
        }
