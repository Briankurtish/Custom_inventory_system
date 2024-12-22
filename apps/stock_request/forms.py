from django import forms
from apps.products.models import Product
from apps.branches.models import Branch

class StockRequestForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="Product", widget=forms.Select(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, label="Quantity", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), label="Branch", widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'worker_profile') and user.worker_profile:
            # Set the initial branch based on the worker's profile
            self.fields['branch'].initial = user.worker_profile.branch
            self.fields['branch'].queryset = Branch.objects.filter(id=user.worker_profile.branch.id)  # Filter the queryset to only include the user's branch
