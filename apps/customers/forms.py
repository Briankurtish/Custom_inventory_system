from django import forms
from .models import Customer
from django.utils.translation import gettext_lazy as _
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name', 'postal_code', 'branch', 'sales_rep', 'contact_person',
            'telephone', 'email', 'agreement_number',
            'tax_payer_number', 'location_plan', 'note',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter customer name')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter postal code')}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'sales_rep': forms.Select(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter Contact Person Name')}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter telephone')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter email')}),
            'agreement_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter agreement number')}),
            'tax_payer_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter tax payer number')}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter Note')}),
        }
        labels = {
            'customer_name': _('Customer Name'),
            'postal_code': _('Postal Code'),
            'branch': _('Branch'),
            'sales_rep': _('Sales Rep'),
            'contact_person': _('Contact Person'),
            'telephone': _('Telephone'),
            'email': _('Email'),
            'agreement_number': _('Agreement Number'),
            'tax_payer_number': _('Tax Payer Number'),
            'location_plan': _('Location Plan'),
            'note': _('Note'),
        }
