from django.db import models
from django.contrib.auth import get_user_model
from apps.customers.models import Customer
from django.utils import timezone

User = get_user_model()

class EmailTemplate(models.Model):
    """Email templates for reusable message formats"""

    TEMPLATE_TYPE_CHOICES = [
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('order_confirmation', 'Order Confirmation'),
        ('invoice_notification', 'Invoice Notification'),
        ('announcement', 'General Announcement'),
        ('welcome', 'Welcome Email'),
        ('custom', 'Custom Message'),
    ]

    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name

class EmailMessage(models.Model):
    """Track sent email messages"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('order_confirmation', 'Order Confirmation'),
        ('invoice_notification', 'Invoice Notification'),
        ('announcement', 'General Announcement'),
        ('welcome', 'Welcome Email'),
        ('custom', 'Custom Message'),
    ]

    recipient_name = models.CharField(max_length=100)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPE_CHOICES, default='custom')
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Message'
        verbose_name_plural = 'Email Messages'

    def __str__(self):
        return f"{self.recipient_name} - {self.subject}"

class EmailGroup(models.Model):
    """Email groups for bulk messaging"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    customers = models.ManyToManyField(Customer, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Group'
        verbose_name_plural = 'Email Groups'

    def __str__(self):
        return self.name

    def get_customer_count(self):
        return self.customers.count()

class EmailLog(models.Model):
    """Log email operations and activities"""

    ACTION_CHOICES = [
        ('send', 'Send Email'),
        ('bulk_send', 'Bulk Send'),
        ('template_create', 'Template Created'),
        ('template_update', 'Template Updated'),
        ('template_delete', 'Template Deleted'),
        ('group_create', 'Group Created'),
        ('group_update', 'Group Updated'),
        ('group_delete', 'Group Deleted'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f"{self.action} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
