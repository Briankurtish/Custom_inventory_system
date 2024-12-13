from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name', 'postal_code', 'sales_rep', 'contact_person',
            'telephone', 'email', 'agreement_number',
            'tax_payer_number', 'location_plan', 'note',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal code'}),
            'sales_rep': forms.Select(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Contact Person Name'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter telephone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'agreement_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter agreement number'}),
            'tax_payer_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax payer number'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Note'}),
        }
        labels = {
            'customer_name': 'Customer Name',
            'postal_code': 'Postal Code',
            'sales_rep': 'Sales Rep',
            'contact_person': 'Contact Person',
            'telephone': 'Telephone',
            'email': 'Email',
            'agreement_number': 'Agreement Number',
            'tax_payer_number': 'Tax Payer Number',
            'location_plan': 'Location Plan',
            'note': 'Note',
        }
