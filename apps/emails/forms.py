from django import forms
from .models import EmailTemplate, EmailGroup, EmailMessage
from apps.customers.models import Customer

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'message', 'template_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Enter email message. Use placeholders like {customer_name}, {amount}, {due_date}'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class EmailGroupForm(forms.ModelForm):
    class Meta:
        model = EmailGroup
        fields = ['name', 'description', 'customers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter group description'
            }),
            'customers': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 10
            })
        }

class SendEmailForm(forms.Form):
    recipient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter recipient email address'
        })
    )
    recipient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter recipient name'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Enter your message'
        })
    )
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="Select a template (optional)",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

class BulkEmailForm(forms.Form):
    EMAIL_TYPE_CHOICES = [
        ('all_customers', 'All Customers'),
        ('selected_group', 'Selected Group'),
        ('selected_customers', 'Selected Customers'),
    ]

    email_type = forms.ChoiceField(
        choices=EMAIL_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    group = forms.ModelChoiceField(
        queryset=EmailGroup.objects.all(),
        required=False,
        empty_label="Select a group",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 10
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Enter your message'
        })
    )
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="Select a template (optional)",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email_type = cleaned_data.get('email_type')
        group = cleaned_data.get('group')
        customers = cleaned_data.get('customers')

        if email_type == 'selected_group' and not group:
            raise forms.ValidationError("Please select a group when sending to selected group.")

        if email_type == 'selected_customers' and not customers:
            raise forms.ValidationError("Please select at least one customer when sending to selected customers.")

        return cleaned_data
