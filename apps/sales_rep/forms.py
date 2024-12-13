from django import forms
from .models import SalesAgent

class SalesAgentForm(forms.ModelForm):
    class Meta:
        model = SalesAgent
        fields = ['agent_firstName', 'agent_lastName', 'telephone', 'email', 'branch', 'agent_manager']
        widgets = {
            'agent_fristName': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agent first name'}),
            'agent_lastName': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agent last name'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'agent_manager': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agent manager'}),
        }
        labels = {
            'agent_fristName': 'Sales Agent First Name',
            'agent_lastName': 'Sales Agent Last Name',
            'telephone': 'Telephone',
            'email': 'Email',
            'branch': 'Branch',
            'agent_manager': "Agent's Manager",
        }
