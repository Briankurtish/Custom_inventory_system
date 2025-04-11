from django import forms
from apps.products.models import Product
from django.db.models import F
from apps.branches.models import Branch
from .models import StockRequestDocument, StockTransferDocument


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

        # Handle branch field based on user permissions
        if user:
            if user.is_superuser:
                # Superusers see all branches
                self.fields['branch'].queryset = Branch.objects.all()
            elif hasattr(user, 'worker_profile') and user.worker_profile:
                # Regular users see only their assigned branch
                user_branch = user.worker_profile.branch
                self.fields['branch'].initial = user_branch
                self.fields['branch'].queryset = Branch.objects.filter(id=user_branch.id)
            else:
                # If user has no worker profile, show no branches
                self.fields['branch'].queryset = Branch.objects.none()
        else:
            self.fields['branch'].queryset = Branch.objects.none()

        # Filter products with stock in the Central Warehouse
        central_warehouse = Branch.objects.filter(branch_name="Central Warehouse").first()
        if central_warehouse:
            # Filter products that have stock in the Central Warehouse with their associated batch
            products_with_stock = Product.objects.filter(
                stocks__branch=central_warehouse,
                stocks__batch=F('batch'),  # Ensure the stock's batch matches the product's batch
                stocks__total_stock__gt=0
            ).distinct()
            self.fields['product'].queryset = products_with_stock
            if not products_with_stock.exists():
                print("No products with stock found in Central Warehouse.")
        else:
            print("Central Warehouse not found. No products will be available.")
            self.fields['product'].queryset = Product.objects.none()


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
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Optionally set the initial source_branch to the user's branch
        if user and hasattr(user, 'worker_profile'):
            self.fields["source_branch"].initial = user.worker_profile.branch

        # Filter products based on the selected source_branch (if provided in POST data)
        if "source_branch" in self.data:
            try:
                source_branch_id = int(self.data.get("source_branch"))
                branch = Branch.objects.get(id=source_branch_id)
                products_with_stock = Product.objects.filter(
                    stocks__branch=branch,
                    stocks__total_stock__gt=0
                ).distinct()
                self.fields["product"].queryset = products_with_stock
            except (ValueError, Branch.DoesNotExist):
                pass  # If source_branch is invalid, leave product queryset as-is

    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop("user", None)
    #     super().__init__(*args, **kwargs)
    #     if user and hasattr(user, 'worker_profile'):
    #         source_branch = Branch.objects.filter(id=user.worker_profile.branch.id)
    #         self.fields["source_branch"].queryset = source_branch
    #         # Filter products that have stock at the source branch
    #         if source_branch.exists():
    #             branch = source_branch.first()
    #             products_with_stock = Product.objects.filter(
    #                 stocks__branch=branch,  # Changed from stock__branch to stocks__branch
    #                 stocks__total_stock__gt=0
    #             ).distinct()
    #             self.fields["product"].queryset = products_with_stock

    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)

    #     if user:
    #         if user.is_superuser:
    #             self.fields['source_branch'].queryset = Branch.objects.all()
    #             self.fields['destination_branch'].queryset = Branch.objects.all()
    #         elif hasattr(user, 'worker_profile') and user.worker_profile:
    #             user_branch = user.worker_profile.branch
    #             self.fields['source_branch'].queryset = Branch.objects.filter(id=user_branch.id)
    #             self.fields['source_branch'].initial = user_branch
    #             self.fields['destination_branch'].queryset = Branch.objects.exclude(id=user_branch.id)

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



class StockTransferDocumentForm(forms.ModelForm):
    class Meta:
        model = StockTransferDocument
        fields = ['document_type', 'document']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].required = True
        self.fields['document'].required = not self.instance.pk  # Document file is required only for new uploads