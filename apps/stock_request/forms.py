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


class StockTransferForm(forms.Form):
    date_transferred = forms.DateField(
        label="Date Transferred",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    source_branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Source Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destination_branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Destination Branch",
        widget=forms.Select(attrs={'class': 'form-control'})
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

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            if user.is_superuser:
                self.fields['source_branch'].queryset = Branch.objects.all()
                self.fields['destination_branch'].queryset = Branch.objects.all()
            elif hasattr(user, 'worker_profile') and user.worker_profile:
                user_branch = user.worker_profile.branch
                self.fields['source_branch'].queryset = Branch.objects.filter(id=user_branch.id)
                self.fields['source_branch'].initial = user_branch
                self.fields['destination_branch'].queryset = Branch.objects.exclude(id=user_branch.id)

    def clean(self):
        cleaned_data = super().clean()
        source_branch = cleaned_data.get('source_branch')
        destination_branch = cleaned_data.get('destination_branch')
        if source_branch and destination_branch and source_branch == destination_branch:
            raise forms.ValidationError("Source and destination branches cannot be the same.")
        return cleaned_data



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


class ActualTransferQuantityForm(forms.Form):
    date_received = forms.DateField(
        label="Date Received",
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        transfer_items = kwargs.pop('transfer_items', None)
        super().__init__(*args, **kwargs)
        if transfer_items:
            for item in transfer_items:
                self.fields[f'actual_quantity_{item.id}'] = forms.IntegerField(
                    label="Actual Quantity Received for {}".format(item.product.generic_name_dosage),
                    min_value=0,
                    required=True,
                    initial=item.quantity
                )

class StockRequestDocumentForm(forms.ModelForm):
    class Meta:
        model = StockRequestDocument
        fields = ['document_type', 'document']
