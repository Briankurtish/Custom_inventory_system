from django import forms
from .models import ClearanceProcess, ClearanceProcessGroup, ClearanceStep


class ClearanceProcessGroupForm(forms.ModelForm):
    class Meta:
        model = ClearanceProcessGroup
        fields = ['bol_number', 'bol_document']


class ClearanceProcessForm(forms.ModelForm):
    class Meta:
        model = ClearanceProcess
        fields = ['cost', 'document']


class ClearanceStepForm(forms.ModelForm):
    class Meta:
        model = ClearanceStep
        fields = ['step_number', 'name', 'required_document']
