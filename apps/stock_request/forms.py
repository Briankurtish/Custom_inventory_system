from django import forms
from apps.products.models import Product
from apps.branches.models import Branch
class StockRequestForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Product", widget=forms.Select(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, label="Quantity", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), label="Branch", widget=forms.Select(attrs={'class': 'form-control'}))
