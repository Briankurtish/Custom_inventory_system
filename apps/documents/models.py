from django.db import models
from django.utils import timezone
from apps.customers.models import Customer
from apps.workers.models import Worker
import os


class DocumentTemplate(models.Model):
    """
    Store Word document templates that can be used to create client documents.
    Admin/Manager roles can upload and edit templates.
    """
    TEMPLATE_TYPES = [
        ('introductory', 'Introductory Letter'),
        ('follow_up', 'Follow-Up Letter'),
        ('billing', 'Billing Notice'),
        ('legal', 'Legal Notice'),
        ('generic', 'Generic Document'),
    ]

    template_id = models.CharField(max_length=50, unique=True, editable=False)
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, default='generic')
    description = models.TextField(blank=True, null=True)

    # Store both Word file and HTML content for flexibility
    word_file = models.FileField(upload_to='document_templates/', blank=True, null=True)
    html_content = models.TextField(blank=True, null=True, help_text="HTML content for inline editing")

    # Merge field support for future auto-population
    merge_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Available merge fields: {customer_name}, {customer_id}, {contact_person}, {email}, {telephone}, {date}, etc."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_templates'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document Template'
        verbose_name_plural = 'Document Templates'

    def __str__(self):
        return f"{self.template_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.template_id:
            # Generate template ID
            last_template = DocumentTemplate.objects.order_by('id').last()
            new_number = (last_template.id + 1) if last_template else 1
            self.template_id = f"TMPL-{new_number:04d}"
        super().save(*args, **kwargs)


class ClientDocument(models.Model):
    """
    Documents attached to client profiles. Can be created from templates
    or uploaded directly.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('final', 'Final'),
        ('sent', 'Sent'),
        ('archived', 'Archived'),
    ]

    document_id = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_documents',
        help_text="Template used to create this document"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Document content - either file or HTML
    word_file = models.FileField(upload_to='client_documents/', blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_documents'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_documents'
    )

    # Follow-up tracking
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    follow_up_notes = models.TextField(blank=True, null=True)

    # Digital signature placeholder
    is_signed = models.BooleanField(default=False)
    signature_data = models.JSONField(default=dict, blank=True, help_text="Digital signature metadata")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Document'
        verbose_name_plural = 'Client Documents'
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.document_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.document_id:
            # Generate document ID
            customer_prefix = self.customer.customer_id.replace('CUST-', 'DOC-')
            last_doc = ClientDocument.objects.filter(
                document_id__startswith=customer_prefix
            ).order_by('id').last()

            if last_doc:
                last_num = int(last_doc.document_id.split('-')[-1])
                new_number = last_num + 1
            else:
                new_number = 1

            self.document_id = f"{customer_prefix}-{new_number:04d}"

        super().save(*args, **kwargs)

    def get_file_name(self):
        """Get the filename of the attached document"""
        if self.word_file:
            return os.path.basename(self.word_file.name)
        return None


class DocumentVersion(models.Model):
    """
    Track version history of documents with timestamps and user attribution.
    """
    document = models.ForeignKey(
        ClientDocument,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()

    # Store snapshot of content
    word_file = models.FileField(upload_to='document_versions/', blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)

    # Change tracking
    change_summary = models.TextField(blank=True, null=True, help_text="Description of changes made")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_versions'
    )

    class Meta:
        ordering = ['-version_number']
        verbose_name = 'Document Version'
        verbose_name_plural = 'Document Versions'
        unique_together = ['document', 'version_number']

    def __str__(self):
        return f"{self.document.document_id} - v{self.version_number}"


class DocumentFollowUp(models.Model):
    """
    Track follow-up actions and reminders for documents.
    Can be linked to SMS module for automated reminders.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    document = models.ForeignKey(
        ClientDocument,
        on_delete=models.CASCADE,
        related_name='follow_ups'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    due_date = models.DateField()
    reminder_date = models.DateField(blank=True, null=True, help_text="Date to send reminder")

    assigned_to = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_followups'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_followups'
    )
    completed_at = models.DateTimeField(blank=True, null=True)

    # SMS integration placeholder
    sms_reminder_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['due_date', '-priority']
        verbose_name = 'Document Follow-Up'
        verbose_name_plural = 'Document Follow-Ups'
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.document.document_id}"

    def is_overdue(self):
        """Check if follow-up is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date


class DocumentAccessLog(models.Model):
    """
    Audit log for document access and modifications for compliance.
    """
    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('download', 'Downloaded'),
        ('share', 'Shared'),
    ]

    document = models.ForeignKey(
        ClientDocument,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'
        indexes = [
            models.Index(fields=['document', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.document.document_id} at {self.timestamp}"
