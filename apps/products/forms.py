from django import forms
from .models import Batch, Product
from apps.genericName.models import GenericName
from django.utils.translation import gettext_lazy as _


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'generic_name', 'bl_number', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),  # Use date input for expiry date
        }
        labels = {
            'batch_number': _('Batch Number'),  # Translatable label
            'generic_name': _('Generic Name & Dosage'),  # Translatable label
            'bl_number': _('Bill of Lading'),  # Translatable label
            'expiry_date': _('Expiry Date'),  # Translatable label
        }

    # Change 'generic_name' to a ModelChoiceField to fetch data from GenericName table
    generic_name = forms.ModelChoiceField(
        queryset=GenericName.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the generic name from the list")
    )




class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),  # Translatable label
            'brand_name': _('Brand Name'),  # Translatable label
            'pack_size': _('Pack Size'),  # Translatable label
            'batch': _('Batch Number'),  # Translatable label
        }

    def __init__(self, *args, **kwargs):
        has_price_privilege = kwargs.pop('has_price_privilege', False)
        super().__init__(*args, **kwargs)

        if has_price_privilege:
            # Add the unit_price field dynamically
            self.fields['unit_price'] = forms.DecimalField(
                max_digits=10,
                decimal_places=2,
                required=True,
                widget=forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
                help_text=_("Unit Price of the product")
            )
            # Pre-populate with the instance value if available
            if self.instance and self.instance.pk:
                self.fields['unit_price'].initial = self.instance.unit_price

        # Debugging: Check if unit_price is in the form fields
        print("Fields in form:", self.fields.keys())



class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),
            'brand_name': _('Brand Name'),
            'pack_size': _('Pack Size'),
            'batch': _('Batch Number'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the brand_name field with distinct brand names
        self.fields['brand_name'].queryset = GenericName.objects.filter(brand_name__isnull=False).distinct('brand_name')
        self.fields['brand_name'].label_from_instance = lambda obj: obj.brand_name
        self.fields['brand_name'].empty_label = "Select a Brand Name"


class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),  # Translatable label
            'brand_name': _('Brand Name'),  # Translatable label
            'pack_size': _('Pack Size'),  # Translatable label
            'batch': _('Batch Number'),  # Translatable label
        }



class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'batch', 'unit_price']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'unit_price': forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),  # Translatable label
            'brand_name': _('Brand Name'),  # Translatable label
            'pack_size': _('Pack Size'),  # Translatable label
            'batch': _('Batch Number'),  # Translatable label
            'unit_price': _('Unit Price'),  # Translatable label
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill the unit_price if the instance exists
        if self.instance and self.instance.pk:
            self.fields['unit_price'].initial = self.instance.unit_price
