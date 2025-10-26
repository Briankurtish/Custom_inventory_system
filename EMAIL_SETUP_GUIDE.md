# Email Management System Setup Guide

## Overview

This email management system integrates with your existing SMS system to provide comprehensive communication capabilities for GC PHARMA. It uses your existing email server (Hostinger SMTP) for reliable email delivery.

## Current Configuration

Your email system is already configured with:

- **SMTP Server**: smtp.hostinger.com
- **Port**: 587 (TLS)
- **From Email**: info@pharmamgtsystemgc.com
- **Authentication**: Using your existing Hostinger email credentials

## Features Available

### 1. Email Dashboard (`/emails/`)

- Overview of email statistics
- Quick access to all email functions
- Recent email history

### 2. Send Individual Email (`/emails/send/`)

- Send email to specific customers
- Use templates or custom messages
- Support for placeholders: {customer_name}, {amount}, {due_date}

### 3. Bulk Email (`/emails/send/bulk/`)

- Send to customer groups
- Send to all customers
- Select specific customers

### 4. Template Management (`/emails/templates/`)

- Create reusable email templates
- Support for placeholders: {customer_name}, {amount}, {balance}, {due_date}
- Template types: Payment Reminder, Invoice Notification, Welcome Email, etc.

### 5. Group Management (`/emails/groups/`)

- Create customer groups for bulk messaging
- Manage group memberships

### 6. Message History (`/emails/messages/`)

- View all sent emails
- Filter by status, type, date
- Resend failed emails

### 7. Activity Logs (`/emails/logs/`)

- Track all email operations
- Error logging and debugging

## Setup Instructions

### 1. Database Setup ✅ COMPLETED

The email models have been created and migrated:

- EmailTemplate for reusable message formats
- EmailMessage for tracking sent messages
- EmailGroup for bulk messaging
- EmailLog for activity tracking

### 2. Email Service Configuration ✅ COMPLETED

The EmailService class is configured to use your existing Hostinger SMTP settings.

### 3. URL Configuration ✅ COMPLETED

Email URLs are configured under `/emails/` path.

### 4. Admin Interface ✅ COMPLETED

Email models are registered in Django admin for easy management.

## Usage Examples

### Sending a Payment Reminder Email

```python
from apps.emails.services import EmailService
from apps.customers.models import Customer

# Get customer
customer = Customer.objects.get(id=1)

# Send payment reminder
email_service = EmailService()
response = email_service.send_payment_reminder(
    customer=customer,
    amount=150.00,
    due_date='2024-01-15',
    user=request.user
)
```

### Sending Bulk Emails

```python
# Prepare recipients
recipients = [
    {'email': 'customer1@example.com', 'name': 'Customer 1'},
    {'email': 'customer2@example.com', 'name': 'Customer 2'},
]

# Send bulk email
results = email_service.send_bulk_email(
    recipients=recipients,
    subject='Important Update',
    message='Dear {name}, this is an important update...',
    user=request.user
)
```

## Template Placeholders

Use these placeholders in your email templates:

- `{customer_name}` - Customer's name
- `{amount}` - Payment amount
- `{due_date}` - Due date
- `{balance}` - Account balance
- `{invoice_number}` - Invoice number

## Integration with SMS System

The email system works alongside your SMS system:

1. **Unified Dashboard**: Both SMS and Email can be managed from their respective dashboards
2. **Customer Integration**: Both systems use the same customer database
3. **Template System**: Similar template management for both SMS and Email
4. **Group Management**: Customer groups can be used for both SMS and Email

## Email Delivery Limits

With your current Hostinger setup:

- **Daily Limit**: Typically 500-1000 emails per day
- **Rate Limit**: ~10-20 emails per minute
- **Reliability**: High deliverability rate

## Monitoring and Troubleshooting

### Check Email Status

1. Go to `/emails/messages/` to view sent emails
2. Check status: Sent, Failed, Delivered
3. View error messages for failed emails

### Common Issues

1. **Authentication Failed**: Verify EMAIL_HOST_PASSWORD in settings
2. **Connection Timeout**: Check EMAIL_HOST and EMAIL_PORT
3. **Rate Limiting**: Implement delays between bulk sends

### Debug Mode

Enable debug logging in Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'email_debug.log',
        },
    },
    'loggers': {
        'apps.emails': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Security Notes

- Keep your email credentials secure
- Use environment variables for sensitive data
- Monitor email usage and costs
- Implement rate limiting for bulk sends

## Next Steps

1. **Test Email Sending**: Send a test email through the dashboard
2. **Create Templates**: Set up common email templates
3. **Create Groups**: Organize customers into email groups
4. **Set Up Automation**: Create automated email workflows

## Support

For issues with the email system, check:

1. Email logs in the admin panel
2. Django logs for errors
3. Hostinger email settings
4. Network connectivity for SMTP calls

## Cost Considerations

- **Hostinger Email**: Already included in your hosting plan
- **No Additional Costs**: Uses your existing email infrastructure
- **Scalable**: Can handle your business email needs

The email system is now ready to use! You can access it at `/emails/` in your application.
