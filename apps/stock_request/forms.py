from django import forms
from apps.products.models import Product
from apps.branches.models import Branch

class StockRequestForm(forms.Form):
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
