from django import forms
from .models import DocumentTemplate, ClientDocument, DocumentVersion, DocumentFollowUp
from apps.customers.models import Customer
from apps.workers.models import Worker


class DocumentTemplateForm(forms.ModelForm):
    """Form for creating and editing document templates"""

    class Meta:
        model = DocumentTemplate
        fields = [
            'name', 'template_type', 'description',
            'word_file', 'html_content', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this template...'
            }),
            'word_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.doc,.docx'
            }),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        word_file = cleaned_data.get('word_file')
        html_content = cleaned_data.get('html_content')

        if not word_file and not html_content:
            raise forms.ValidationError(
                "Please provide either a Word file or HTML content."
            )

        return cleaned_data


class ClientDocumentForm(forms.ModelForm):
    """Form for creating and editing client documents"""

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'customer-select'
        }),
        label='Customer'
    )

    template = forms.ModelChoiceField(
        queryset=DocumentTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'template-select'
        }),
        label='Select Template (Optional)'
    )

    class Meta:
        model = ClientDocument
        fields = [
            'customer', 'template', 'title', 'description',
            'word_file', 'html_content', 'status',
            'requires_follow_up', 'follow_up_date', 'follow_up_notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description...'
            }),
            'word_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.doc,.docx'
            }),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'requires_follow_up': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'follow_up_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Follow-up notes...'
            })
        }


class ClientDocumentQuickForm(forms.ModelForm):
    """Simplified form for quick document creation"""

    class Meta:
        model = ClientDocument
        fields = ['title', 'word_file', 'html_content', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title'
            }),
            'word_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.doc,.docx'
            }),
            'html_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'id': 'quick-editor'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class DocumentFollowUpForm(forms.ModelForm):
    """Form for creating follow-up tasks"""

    assigned_to = forms.ModelChoiceField(
        queryset=Worker.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Assign To'
    )

    class Meta:
        model = DocumentFollowUp
        fields = [
            'title', 'description', 'priority', 'status',
            'due_date', 'reminder_date', 'assigned_to'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Follow-up title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the follow-up action...'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reminder_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        reminder_date = cleaned_data.get('reminder_date')

        if reminder_date and due_date and reminder_date > due_date:
            raise forms.ValidationError(
                "Reminder date cannot be after due date."
            )

        return cleaned_data


class DocumentSearchForm(forms.Form):
    """Form for searching and filtering documents"""

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Customer'
    )

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ClientDocument.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status'
    )

    template_type = forms.ChoiceField(
        choices=[('', 'All Types')] + DocumentTemplate.TEMPLATE_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Template Type'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )

    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents...'
        }),
        label='Search'
    )
