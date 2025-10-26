from django import forms
from django.contrib.auth import get_user_model
from .models import SMSTemplate, SMSGroup, SMSMessage
from apps.customers.models import Customer

User = get_user_model()

class SMSTemplateForm(forms.ModelForm):
    """Form for creating and editing SMS templates"""

    class Meta:
        model = SMSTemplate
        fields = ['name', 'subject', 'message', 'template_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter message subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your message template. Use {customer_name}, {amount}, {balance}, {due_date} as placeholders.'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class SMSGroupForm(forms.ModelForm):
    """Form for creating and editing SMS groups"""

    class Meta:
        model = SMSGroup
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

class SendSMSForm(forms.Form):
    """Form for sending individual SMS messages"""

    MESSAGE_TYPE_CHOICES = [
        ('', 'Select message type'),
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('announcement', 'General Announcement'),
        ('order_update', 'Order Update'),
        ('custom', 'Custom Message'),
    ]

    recipient_type = forms.ChoiceField(
        choices=[
            ('customer', 'Select Customer'),
            ('manual', 'Enter Manually'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="Select a customer",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    recipient_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter recipient name'
        })
    )

    recipient_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number (e.g., +1234567890)'
        })
    )

    template = forms.ModelChoiceField(
        queryset=SMSTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="Select a template (optional)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message subject'
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your message'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        customer = cleaned_data.get('customer')
        recipient_name = cleaned_data.get('recipient_name')
        recipient_phone = cleaned_data.get('recipient_phone')

        if recipient_type == 'customer':
            if not customer:
                raise forms.ValidationError('Please select a customer.')
        elif recipient_type == 'manual':
            if not recipient_name:
                raise forms.ValidationError('Please enter recipient name.')
            if not recipient_phone:
                raise forms.ValidationError('Please enter recipient phone number.')

        return cleaned_data

class BulkSMSForm(forms.Form):
    """Form for sending bulk SMS messages"""

    MESSAGE_TYPE_CHOICES = [
        ('', 'Select message type'),
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('announcement', 'General Announcement'),
        ('order_update', 'Order Update'),
        ('custom', 'Custom Message'),
    ]

    recipient_type = forms.ChoiceField(
        choices=[
            ('group', 'Send to Group'),
            ('all_customers', 'Send to All Customers'),
            ('customers', 'Select Specific Customers'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    group = forms.ModelChoiceField(
        queryset=SMSGroup.objects.all(),
        required=False,
        empty_label="Select a group",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    customers = forms.ModelMultipleChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 10
        })
    )

    template = forms.ModelChoiceField(
        queryset=SMSTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="Select a template (optional)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message subject'
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your message'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        group = cleaned_data.get('group')
        customers = cleaned_data.get('customers')

        if recipient_type == 'group':
            if not group:
                raise forms.ValidationError('Please select a group.')
        elif recipient_type == 'customers':
            if not customers:
                raise forms.ValidationError('Please select at least one customer.')

        return cleaned_data

class SMSFilterForm(forms.Form):
    """Form for filtering SMS messages"""

    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('undelivered', 'Undelivered'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('', 'All Types'),
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('announcement', 'General Announcement'),
        ('order_update', 'Order Update'),
        ('custom', 'Custom Message'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by recipient name or phone...'
        })
    )
