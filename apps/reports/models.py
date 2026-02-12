from django.db import models
from apps.workers.models import Worker


class SavedReport(models.Model):
    """Model to save custom report configurations"""
    REPORT_TYPE_CHOICES = [
        ('client_financial', 'Client Financial'),
        ('regional_performance', 'Regional Performance'),
        ('sales_agent_performance', 'Sales Agent Performance'),
        ('inventory', 'Inventory & Products'),
        ('financial_summary', 'Financial Summary'),
        ('debt_analysis', 'Debt Analysis'),
        ('payment_analysis', 'Payment Analysis'),
    ]

    name = models.CharField(max_length=200, help_text="Name of the saved report")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)

    # Filters stored as JSON
    filters = models.JSONField(default=dict, blank=True)

    # Access control
    created_by = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name='created_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Sharing
    is_shared = models.BooleanField(default=False, help_text="Make this report visible to other users")
    shared_with_roles = models.JSONField(
        default=list, blank=True,
        help_text="List of roles that can access this report"
    )

    # Schedule
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Saved Report"
        verbose_name_plural = "Saved Reports"

    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"


class ReportExport(models.Model):
    """Track report exports"""
    EXPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]

    report = models.ForeignKey(SavedReport, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=50)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMAT_CHOICES)
    file_path = models.FileField(upload_to='report_exports/', null=True, blank=True)

    exported_by = models.ForeignKey(Worker, on_delete=models.CASCADE)
    exported_at = models.DateTimeField(auto_now_add=True)

    # Metadata
    filters_applied = models.JSONField(default=dict)
    record_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-exported_at']
        verbose_name = "Report Export"
        verbose_name_plural = "Report Exports"

    def __str__(self):
        return f"{self.report_type} - {self.export_format} - {self.exported_at.strftime('%Y-%m-%d')}"


class ReportAccessLog(models.Model):
    """Log report access for audit purposes"""
    report = models.ForeignKey(SavedReport, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=50)
    accessed_by = models.ForeignKey(Worker, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)
    filters_used = models.JSONField(default=dict)

    class Meta:
        ordering = ['-accessed_at']
        verbose_name = "Report Access Log"
        verbose_name_plural = "Report Access Logs"

    def __str__(self):
        return f"{self.report_type} accessed by {self.accessed_by.employee_id} at {self.accessed_at}"
