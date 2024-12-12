from django import forms
from .models import Branch

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['branch_id', 'branch_name', 'address']
        widgets = {
            'branch_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Branch ID'}),
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Branch Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Branch Address', 'rows': 3}),
        }
        labels = {
            'branch_id': 'Branch ID',
            'branch_name': 'Branch Name',
            'address': 'Address',
        }
