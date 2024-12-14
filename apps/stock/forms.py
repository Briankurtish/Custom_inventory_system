from django import forms
from .models import Stock  # Import your Branch model

class StockUpdateForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ('product', 'quantity', 'branch')