from django.contrib import admin
from .models import SavedReport, ReportExport, ReportAccessLog


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'created_at', 'is_shared', 'is_scheduled']
    list_filter = ['report_type', 'is_shared', 'is_scheduled', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Filters & Configuration', {
            'fields': ('filters',)
        }),
        ('Access Control', {
            'fields': ('created_by', 'is_shared', 'shared_with_roles')
        }),
        ('Schedule', {
            'fields': ('is_scheduled', 'schedule_frequency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'export_format', 'exported_by', 'exported_at', 'record_count']
    list_filter = ['export_format', 'exported_at', 'report_type']
    search_fields = ['report_type']
    readonly_fields = ['exported_at']


@admin.register(ReportAccessLog)
class ReportAccessLogAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'accessed_by', 'accessed_at']
    list_filter = ['report_type', 'accessed_at']
    search_fields = ['report_type', 'accessed_by__employee_id']
    readonly_fields = ['accessed_at']
