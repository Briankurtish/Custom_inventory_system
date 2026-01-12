from django import forms
from .models import GenericName
from django.utils.translation import gettext_lazy as _

class GenericNameForm(forms.ModelForm):
    # Override generic_name to be a ChoiceField with Select2
    generic_name = forms.CharField(
        max_length=255,
        label=_('Generic Name'),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-placeholder': _('Search or enter Generic Name')
        }),
        help_text=_('Type a new generic name or select an existing one from the dropdown')
    )
    
    class Meta:
        model = GenericName
        fields = ['generic_name', 'brand_name', 'old_brand_name']
        widgets = {
            'brand_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter Brand Name (optional)')
            }),
            'old_brand_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Enter Old Brand Name (optional)')
            }),
        }
        labels = {
            'brand_name': _('Brand Name'),
            'old_brand_name': _('Old Brand Name'),
        }
        help_texts = {
            'brand_name': _('Add a different brand name for the same generic name'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get distinct generic names for the dropdown choices
        existing_names = GenericName.objects.values_list(
            'generic_name', flat=True
        ).distinct().order_by('generic_name')
        
        # Create choices list with empty option at the start
        choices = [('', '---------')]
        choices.extend([(name, name) for name in existing_names])
        
        # Set choices for the select field
        self.fields['generic_name'].widget.choices = choices
        
        # Pre-fill with instance value if editing
        if self.instance and self.instance.pk:
            self.fields['generic_name'].initial = self.instance.generic_name