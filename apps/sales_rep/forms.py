from django import forms
from .models import SalesAgent

class SalesAgentForm(forms.ModelForm):
    class Meta:
        model = SalesAgent
        fields = ['agent_name', 'telephone', 'email', 'branch']
        widgets = {
            'agent_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agent name'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'agent_name': 'Sales Agent Name',
            'telephone': 'Telephone',
            'email': 'Email',
            'branch': 'Branch',
        }
