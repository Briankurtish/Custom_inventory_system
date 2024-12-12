from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name', 'postal_code', 'contact_person',
            'telephone', 'email', 'agreement_number',
            'tax_payer_number', 'location_plan',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal code'}),
            'contact_person': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'agreement_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agreement number'}),
            'tax_payer_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax payer number'}),
        }
        labels = {
            'customer_name': 'Customer Name',
            'postal_code': 'Postal Code',
            'contact_person': 'Contact Person',
            'telephone': 'Telephone',
            'email': 'Email',
            'agreement_number': 'Agreement Number',
            'tax_payer_number': 'Tax Payer Number',
            'location_plan': 'Location Plan',
        }
