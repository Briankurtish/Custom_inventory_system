from django import forms
from .models import Batch, DosageForm, DosageType, Product
from apps.genericName.models import GenericName
from django.utils.translation import gettext_lazy as _


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'generic_name', 'bl_number', 'prod_date', 'expiry_date']
        widgets = {
            'prod_date': forms.DateInput(attrs={'type': 'date'}),  # Use date input for expiry date
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),  # Use date input for expiry date
        }
        labels = {
            'batch_number': _('Batch Number'),  # Translatable label
            'generic_name': _('Generic Name & Dosage'),  # Translatable label
            'bl_number': _('Bill of Lading'),  # Translatable label
            'prod_date': _('Manufacturing Date'),  # Translatable label
            'expiry_date': _('Expiration Date'),  # Translatable label
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
        fields = ['generic_name_dosage', 'brand_name', 'dosage_form', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),  # Translatable label
            'brand_name': _('Brand Name'),  # Translatable label
            'dosage_form': _('Dosage Form'),  # Translatable label
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
        fields = ['generic_name_dosage', 'brand_name', 'dosage_form', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),
            'brand_name': _('Brand Name'),
            'dosage_form': _('Dosage Form'),
            # 'dosage_type': _('Dosage Type'),
            'pack_size': _('Pack Size'),
            'batch': _('Batch Number'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically update brand_name and batch based on selected generic_name_dosage
        if 'generic_name_dosage' in self.data:
            generic_name_id = self.data.get('generic_name_dosage')
            if generic_name_id:
                # Filter brand_name based on the selected generic_name_dosage
                self.fields['brand_name'].queryset = GenericName.objects.filter(id=generic_name_id)
                # Filter batch based on the selected generic_name_dosage
                self.fields['batch'].queryset = Batch.objects.filter(generic_name_id=generic_name_id)
        elif self.instance.pk:
            # If the instance exists, set brand_name and batch based on the related GenericName
            self.fields['brand_name'].queryset = GenericName.objects.filter(id=self.instance.generic_name_dosage.id)
            self.fields['batch'].queryset = Batch.objects.filter(generic_name=self.instance.generic_name_dosage)

        # You may also want to filter distinct brand names for the select dropdowns (optional)
        brand_names = GenericName.objects.exclude(brand_name__isnull=True).exclude(brand_name="").values_list('brand_name', flat=True).distinct()
        self.fields['brand_name'].queryset = GenericName.objects.filter(brand_name__in=brand_names)
        self.fields['brand_name'].label_from_instance = lambda obj: obj.brand_name
        self.fields['brand_name'].empty_label = "Select a Brand Name"



class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'dosage_form', 'dosage_type', 'pack_size', 'batch']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),
            'brand_name': _('Brand Name'),
            'dosage_form': _('Dosage Form'),
            'dosage_type': _('Dosage Type'),
            'pack_size': _('Pack Size'),
            'batch': _('Batch Number'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get distinct brand names
        brand_names = GenericName.objects.exclude(brand_name__isnull=True).exclude(brand_name="").values_list('brand_name', flat=True).distinct()
        self.fields['brand_name'].queryset = GenericName.objects.filter(brand_name__in=brand_names)
        self.fields['brand_name'].label_from_instance = lambda obj: obj.brand_name
        self.fields['brand_name'].empty_label = "Select a Brand Name"



class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['generic_name_dosage', 'brand_name', 'pack_size', 'dosage_form', 'dosage_type', 'batch', 'unit_price']
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'unit_price': forms.NumberInput(attrs={'type': 'number', 'class': 'form-control'}),
        }
        labels = {
            'generic_name_dosage': _('Generic Name & Dosage'),  # Translatable label
            'brand_name': _('Brand Name'),  # Translatable label
            'dosage_form': _('Dosage Form'),  # Translatable label
            'dosage_type': _('Dosage Type'),  # Translatable label
            'pack_size': _('Pack Size'),  # Translatable label
            'batch': _('Batch Number'),  # Translatable label
            'unit_price': _('Unit Price'),  # Translatable label
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        brand_names = GenericName.objects.exclude(brand_name__isnull=True).exclude(brand_name="").values_list('brand_name', flat=True).distinct()
        self.fields['brand_name'].queryset = GenericName.objects.filter(brand_name__in=brand_names)
        self.fields['brand_name'].label_from_instance = lambda obj: obj.brand_name
        self.fields['brand_name'].empty_label = "Select a Brand Name"
        # Pre-fill the unit_price if the instance exists
        if self.instance and self.instance.pk:
            self.fields['unit_price'].initial = self.instance.unit_price


class DosageFormForm(forms.ModelForm):
    class Meta:
        model = DosageForm
        fields = ['name']
        labels = {
            'name': 'Dosage Form',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Dosage Form'}),
        }

class DosageTypeForm(forms.ModelForm):
    class Meta:
        model = DosageType
        fields = ['dosage_form', 'name']  # Include dosage_form
        labels = {
            'dosage_form': 'Dosage Form',
            'name': 'Dosage Type',
        }
        widgets = {
            'dosage_form': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for ForeignKey
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Dosage Type'}),
        }
