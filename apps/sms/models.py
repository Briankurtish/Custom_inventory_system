from django.db import models
from django.contrib.auth import get_user_model
from apps.customers.models import Customer
from apps.workers.models import Worker
from datetime import datetime

User = get_user_model()

class SMSTemplate(models.Model):
    """Template for SMS messages"""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    template_type = models.CharField(
        max_length=50,
        choices=[
            ('payment_reminder', 'Payment Reminder'),
            ('balance_notification', 'Balance Notification'),
            ('announcement', 'General Announcement'),
            ('order_update', 'Order Update'),
            ('custom', 'Custom Message'),
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sms_templates'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class SMSMessage(models.Model):
    """Individual SMS message record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('undelivered', 'Undelivered'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('payment_reminder', 'Payment Reminder'),
        ('balance_notification', 'Balance Notification'),
        ('announcement', 'General Announcement'),
        ('order_update', 'Order Update'),
        ('custom', 'Custom Message'),
    ]

    # Message details
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPE_CHOICES)

    # Template reference
    template = models.ForeignKey(
        SMSTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_messages'
    )

    # Customer reference (if applicable)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_messages'
    )

    # Twilio details
    twilio_sid = models.CharField(max_length=100, blank=True, null=True)
    twilio_status = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # User who sent the message
    sent_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_sms_messages'
    )

    # Error details
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SMS to {self.recipient_name} ({self.recipient_phone}) - {self.status}"

class SMSGroup(models.Model):
    """Group of customers for bulk SMS sending"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    customers = models.ManyToManyField(Customer, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sms_groups'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_customer_count(self):
        return self.customers.count()

class SMSLog(models.Model):
    """Log for SMS operations and errors"""
    ACTION_CHOICES = [
        ('send', 'Send Message'),
        ('bulk_send', 'Bulk Send'),
        ('template_create', 'Create Template'),
        ('template_update', 'Update Template'),
        ('group_create', 'Create Group'),
        ('error', 'Error'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField()
    user = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_error = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.timestamp}"
