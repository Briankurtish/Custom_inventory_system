from django import forms
from .models import Recommendation

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['pharmacist','product', 'quantity', 'reason', 'recommendation_document']
        widgets = {
            'pharmacist': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Product'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter reason (optional)'}),
        }
        labels = {
            'pharmacist': 'Pharmacist',
            'product': 'Product',
            'quantity': 'Quantity',
            'reason': 'Reason',
            'recommendation_document': 'Recommendation Document',
        }
