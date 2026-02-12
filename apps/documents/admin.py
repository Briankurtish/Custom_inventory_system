from django.contrib import admin
from .models import (
    DocumentTemplate, ClientDocument, DocumentVersion,
    DocumentFollowUp, DocumentAccessLog
)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_id', 'name', 'template_type', 'is_active', 'created_at', 'created_by']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'template_id', 'description']
    readonly_fields = ['template_id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('template_id', 'name', 'template_type', 'description', 'is_active')
        }),
        ('Content', {
            'fields': ('word_file', 'html_content', 'merge_fields')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.worker_profile
        obj.updated_by = request.user.worker_profile
        super().save_model(request, obj, form, change)


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_id', 'title', 'customer', 'status', 'created_at', 'created_by', 'requires_follow_up']
    list_filter = ['status', 'requires_follow_up', 'created_at', 'template__template_type']
    search_fields = ['document_id', 'title', 'customer__customer_name', 'customer__customer_id']
    readonly_fields = ['document_id', 'created_at', 'updated_at']
    raw_id_fields = ['customer', 'template']

    fieldsets = (
        ('Basic Information', {
            'fields': ('document_id', 'customer', 'template', 'title', 'description', 'status')
        }),
        ('Content', {
            'fields': ('word_file', 'html_content')
        }),
        ('Follow-up', {
            'fields': ('requires_follow_up', 'follow_up_date', 'follow_up_notes'),
            'classes': ('collapse',)
        }),
        ('Digital Signature', {
            'fields': ('is_signed', 'signature_data'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.worker_profile
        obj.updated_by = request.user.worker_profile
        super().save_model(request, obj, form, change)


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'created_at', 'created_by']
    list_filter = ['created_at']
    search_fields = ['document__document_id', 'document__title', 'change_summary']
    readonly_fields = ['created_at']
    raw_id_fields = ['document']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.worker_profile
        super().save_model(request, obj, form, change)


@admin.register(DocumentFollowUp)
class DocumentFollowUpAdmin(admin.ModelAdmin):
    list_display = ['title', 'document', 'priority', 'status', 'due_date', 'assigned_to']
    list_filter = ['priority', 'status', 'due_date']
    search_fields = ['title', 'description', 'document__document_id', 'document__title']
    readonly_fields = ['created_at', 'completed_at', 'sms_sent_at']
    raw_id_fields = ['document', 'assigned_to']
    date_hierarchy = 'due_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('document', 'title', 'description', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'due_date', 'reminder_date')
        }),
        ('SMS Integration', {
            'fields': ('sms_reminder_sent', 'sms_sent_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.worker_profile
        super().save_model(request, obj, form, change)


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'document', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__user__username', 'document__document_id', 'document__title']
    readonly_fields = ['timestamp']
    raw_id_fields = ['document', 'user']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # Prevent manual creation of logs
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing of logs
        return False
