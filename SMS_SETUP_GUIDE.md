# SMS System Setup Guide

## Overview

This SMS system integrates with Twilio to send automated notifications, payment reminders, and balance updates to your customers.

## Setup Instructions

### 1. Twilio Account Setup

1. Go to [Twilio Console](https://console.twilio.com/)
2. Get your Account SID and Auth Token from the dashboard
3. Purchase a phone number for sending SMS

### 2. Environment Configuration

Add these environment variables to your `.env` file:

```bash
# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
```

### 3. Database Migration

The SMS models have been created and migrated. The system includes:

- SMS Templates for reusable message formats
- SMS Messages for tracking sent messages
- SMS Groups for bulk messaging
- SMS Logs for activity tracking

### 4. Features Available

#### SMS Dashboard (`/sms/`)

- Overview of SMS statistics
- Quick access to all SMS functions
- Recent message history

#### Send Individual SMS (`/sms/send/`)

- Send SMS to specific customers
- Use templates or custom messages
- Real-time character counting

#### Bulk SMS (`/sms/send/bulk/`)

- Send to customer groups
- Send to all customers
- Select specific customers

#### Template Management (`/sms/templates/`)

- Create reusable message templates
- Support for placeholders: {customer_name}, {amount}, {balance}, {due_date}
- Template types: Payment Reminder, Balance Notification, Announcement, etc.

#### Group Management (`/sms/groups/`)

- Create customer groups for bulk messaging
- Manage group memberships

#### Message History (`/sms/messages/`)

- View all sent messages
- Filter by status, type, date
- Resend failed messages

#### Activity Logs (`/sms/logs/`)

- Track all SMS operations
- Error logging and debugging

### 5. Automated Notifications

#### Management Command

Use the management command to send automated notifications:

```bash
# Send payment reminders
python manage.py send_notifications --payment-reminders

# Send balance notifications
python manage.py send_notifications --balance-notifications

# Send all notifications
python manage.py send_notifications --all

# Dry run (see what would be sent)
python manage.py send_notifications --all --dry-run
```

#### Cron Job Setup

Add to your crontab for automated sending:

```bash
# Send payment reminders daily at 9 AM
0 9 * * * cd /path/to/your/project && source /opt/myproject/bin/activate && python manage.py send_notifications --payment-reminders

# Send balance notifications weekly on Monday at 10 AM
0 10 * * 1 cd /path/to/your/project && source /opt/myproject/bin/activate && python manage.py send_notifications --balance-notifications
```

### 6. Integration with Main Dashboard

The SMS system is integrated into the main dashboard with a quick access card.

### 7. Customization

#### Adding New Template Types

Edit `apps/sms/models.py` to add new template types:

```python
TEMPLATE_TYPE_CHOICES = [
    ('payment_reminder', 'Payment Reminder'),
    ('balance_notification', 'Balance Notification'),
    ('announcement', 'General Announcement'),
    ('order_update', 'Order Update'),
    ('your_new_type', 'Your New Type'),  # Add here
    ('custom', 'Custom Message'),
]
```

#### Customizing Notification Logic

Edit `apps/sms/management/commands/send_notifications.py` to implement your specific business logic for:

- Payment reminders (outstanding invoices, due dates)
- Balance notifications (account balances, credit limits)

### 8. Security Notes

- Keep your Twilio credentials secure
- Use environment variables for sensitive data
- Monitor SMS usage and costs
- Implement rate limiting if needed

### 9. Troubleshooting

#### Common Issues

1. **Twilio credentials not working**: Verify Account SID, Auth Token, and phone number
2. **Messages not sending**: Check phone number format (include country code)
3. **Template placeholders not working**: Ensure placeholders match exactly: {customer_name}, {amount}, etc.

#### Debug Mode

Enable debug logging in Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'sms_debug.log',
        },
    },
    'loggers': {
        'apps.sms': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 10. Support

For issues with the SMS system, check:

1. Twilio Console for delivery status
2. SMS logs in the admin panel
3. Django logs for errors
4. Network connectivity for Twilio API calls
