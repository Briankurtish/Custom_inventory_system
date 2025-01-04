from django import forms
from .models import Branch

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_name', 'address', 'branch_type']  # Added 'branch_type'
        widgets = {
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Branch Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Branch Address', 'rows': 3}),
            'branch_type': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for branch type
        }
        labels = {
            'branch_name': 'Branch Name',
            'address': 'Address',
            'branch_type': 'Branch Type',  # Label for branch type
        }
