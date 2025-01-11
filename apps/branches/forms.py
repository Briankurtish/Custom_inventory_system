from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Branch

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_name', 'address', 'branch_type']  # Added 'branch_type'
        widgets = {
            'branch_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter Branch Name')  # Translatable placeholder
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter Branch Address'),  # Translatable placeholder
                'rows': 3
            }),
            'branch_type': forms.Select(attrs={
                'class': 'form-control'
            }),  # Dropdown for branch type
        }
        labels = {
            'branch_name': _('Branch Name'),  # Translatable label
            'address': _('Address'),  # Translatable label
            'branch_type': _('Branch Type'),  # Translatable label
        }
