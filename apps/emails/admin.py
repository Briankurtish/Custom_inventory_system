from django.contrib import admin
from .models import EmailTemplate, EmailMessage, EmailGroup, EmailLog

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at', 'created_by']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Content', {
            'fields': ('subject', 'message')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'recipient_email', 'subject', 'message_type', 'status', 'sent_at']
    list_filter = ['message_type', 'status', 'sent_at', 'created_at']
    search_fields = ['recipient_name', 'recipient_email', 'subject']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at']
    fieldsets = (
        ('Recipient Information', {
            'fields': ('recipient_name', 'recipient_email', 'customer')
        }),
        ('Message Content', {
            'fields': ('subject', 'message', 'template', 'message_type')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'sent_at', 'delivered_at', 'error_message')
        }),
        ('Metadata', {
            'fields': ('sent_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EmailGroup)
class EmailGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_customer_count', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['customers']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Customers', {
            'fields': ('customers',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'is_error', 'created_at']
    list_filter = ['action', 'is_error', 'created_at']
    search_fields = ['details', 'user__username']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Log Information', {
            'fields': ('action', 'details', 'user', 'is_error')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
