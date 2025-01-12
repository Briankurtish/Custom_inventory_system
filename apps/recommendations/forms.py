from django import forms
from .models import Recommendation
from django.utils.translation import gettext_lazy as _

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['product', 'quantity', 'reason', 'recommendation_document']  # Removed 'pharmacist'
        widgets = {
            'product': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter Product')}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Enter quantity')}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter reason (optional)')}),
        }
        labels = {
            'product': _('Product'),
            'quantity': _('Quantity'),
            'reason': _('Reason'),
            'recommendation_document': _('Recommendation Document'),
        }