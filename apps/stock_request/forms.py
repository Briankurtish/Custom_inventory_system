from django import forms
from apps.products.models import Product
from apps.branches.models import Branch
from .models import StockRequestDocument


class StockRequestForm(forms.Form):
    requested_at = forms.DateField(
        label="Date Requested",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)

        if user:
            if user.is_superuser:
                # Superusers see all branches
                self.fields['branch'].queryset = Branch.objects.all()
            elif hasattr(user, 'worker_profile') and user.worker_profile:
                # Regular users see only their assigned branch
                user_branch = user.worker_profile.branch
                self.fields['branch'].initial = user_branch
                self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)


class ActualQuantityForm(forms.Form):
    date_received = forms.DateField(
        label="Date Received",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        in_transit_items = kwargs.pop('in_transit_items', [])
        super().__init__(*args, **kwargs)

        # Dynamically add fields for each in-transit item
        for item in in_transit_items:
            self.fields[f'actual_quantity_{item.id}'] = forms.IntegerField(
                label=f"Actual Quantity Received for {item.product.generic_name_dosage}",
                min_value=0,
                required=True,
                initial=0
            )


class StockRequestDocumentForm(forms.ModelForm):
    class Meta:
        model = StockRequestDocument
        fields = ['document_type', 'document']
