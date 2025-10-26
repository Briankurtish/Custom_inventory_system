from django.contrib import admin
from .models import SMSTemplate, SMSMessage, SMSGroup, SMSLog

@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at', 'created_by']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'message']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'subject', 'message', 'template_type', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'recipient_phone', 'message_type', 'status', 'created_at', 'sent_by']
    list_filter = ['status', 'message_type', 'created_at', 'sent_at']
    search_fields = ['recipient_name', 'recipient_phone', 'message']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'twilio_sid', 'twilio_status']

    fieldsets = (
        ('Message Information', {
            'fields': ('recipient_name', 'recipient_phone', 'subject', 'message', 'message_type')
        }),
        ('Template & Customer', {
            'fields': ('template', 'customer'),
            'classes': ('collapse',)
        }),
        ('Status & Twilio', {
            'fields': ('status', 'twilio_sid', 'twilio_status', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('sent_by',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SMSGroup)
class SMSGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_customer_count', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['customers']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'description', 'customers')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'timestamp', 'is_error']
    list_filter = ['action', 'is_error', 'timestamp']
    search_fields = ['details', 'user__username']
    readonly_fields = ['timestamp']

    fieldsets = (
        ('Log Information', {
            'fields': ('action', 'details', 'is_error')
        }),
        ('Metadata', {
            'fields': ('user', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
