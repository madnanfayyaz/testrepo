"""
Reporting & Dashboards Models
4 models: Dashboard, DashboardWidget, Report, ReportSchedule
"""

from django.db import models
from django.utils import timezone
import uuid


class Dashboard(models.Model):
    """
    Custom dashboard configuration.
    Users can create custom dashboards with multiple widgets.
    """
    DASHBOARD_TYPE_CHOICES = [
        ('executive', 'Executive Overview'),
        ('compliance', 'Compliance Status'),
        ('findings', 'Findings & Remediation'),
        ('assessment', 'Assessment Progress'),
        ('custom', 'Custom Dashboard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='dashboards'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(
        max_length=50,
        choices=DASHBOARD_TYPE_CHOICES,
        default='custom'
    )
    
    # Ownership
    created_by = models.ForeignKey(
        'iam.AppUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='dashboards_created'
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Is this the default dashboard for the tenant?"
    )
    is_shared = models.BooleanField(
        default=False,
        help_text="Is this dashboard shared with all users?"
    )
    
    # Layout configuration
    layout_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dashboard layout configuration"
    )
    
    # Refresh settings
    auto_refresh = models.BooleanField(default=False)
    refresh_interval = models.IntegerField(
        default=300,
        help_text="Auto-refresh interval in seconds"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_default']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_dashboard_type_display()})"
    
    def get_widget_count(self):
        """Count widgets in this dashboard"""
        return self.widgets.count()


class DashboardWidget(models.Model):
    """
    Individual widget/chart on a dashboard.
    """
    WIDGET_TYPE_CHOICES = [
        ('metric_card', 'Metric Card'),
        ('bar_chart', 'Bar Chart'),
        ('line_chart', 'Line Chart'),
        ('pie_chart', 'Pie Chart'),
        ('donut_chart', 'Donut Chart'),
        ('table', 'Data Table'),
        ('gauge', 'Gauge'),
        ('trend', 'Trend Line'),
        ('progress_bar', 'Progress Bar'),
    ]
    
    DATA_SOURCE_CHOICES = [
        ('assessments', 'Assessments'),
        ('findings', 'Findings'),
        ('responses', 'Responses'),
        ('remediation', 'Remediation'),
        ('controls', 'Controls'),
        ('custom', 'Custom Query'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='dashboard_widgets'
    )
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    
    # Widget configuration
    title = models.CharField(max_length=255)
    widget_type = models.CharField(
        max_length=50,
        choices=WIDGET_TYPE_CHOICES
    )
    data_source = models.CharField(
        max_length=50,
        choices=DATA_SOURCE_CHOICES
    )
    
    # Data configuration
    query_config = models.JSONField(
        default=dict,
        help_text="Query configuration (filters, parameters)"
    )
    chart_config = models.JSONField(
        default=dict,
        help_text="Chart styling and display options"
    )
    
    # Layout
    position_x = models.IntegerField(default=0, help_text="X position in grid")
    position_y = models.IntegerField(default=0, help_text="Y position in grid")
    width = models.IntegerField(default=4, help_text="Width in grid units (1-12)")
    height = models.IntegerField(default=4, help_text="Height in grid units")
    
    # Display options
    show_legend = models.BooleanField(default=True)
    show_title = models.BooleanField(default=True)
    
    # Caching
    cache_duration = models.IntegerField(
        default=300,
        help_text="Cache duration in seconds"
    )
    last_cached = models.DateTimeField(null=True, blank=True)
    cached_data = models.JSONField(null=True, blank=True)
    
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_widget'
        ordering = ['dashboard', 'display_order']
        indexes = [
            models.Index(fields=['tenant', 'dashboard']),
            models.Index(fields=['data_source']),
        ]
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class Report(models.Model):
    """
    Generated report (PDF, Excel, CSV, HTML).
    """
    REPORT_TYPE_CHOICES = [
        ('assessment_summary', 'Assessment Summary'),
        ('findings_report', 'Findings Report'),
        ('compliance_status', 'Compliance Status'),
        ('executive_summary', 'Executive Summary'),
        ('gap_analysis', 'Gap Analysis'),
        ('remediation_plan', 'Remediation Plan'),
        ('control_matrix', 'Control Matrix'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    # Report configuration
    name = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default='pdf'
    )
    description = models.TextField(blank=True)
    
    # Scope
    assessment = models.ForeignKey(
        'assessments.Assessment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports',
        help_text="Assessment this report is for (if applicable)"
    )
    
    # Parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Report generation parameters"
    )
    
    # Generation
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated report file"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    # Ownership
    generated_by = models.ForeignKey(
        'iam.AppUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports_generated'
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['assessment']),
            models.Index(fields=['generated_by']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_format_display()})"
    
    def mark_as_generating(self):
        """Mark report as generating"""
        self.status = 'generating'
        self.save()
    
    def mark_as_completed(self, file_path, file_size):
        """Mark report as completed"""
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.generated_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark report as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()


class ReportSchedule(models.Model):
    """
    Scheduled report generation.
    Automatically generates reports on a schedule.
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='report_schedules'
    )
    
    # Schedule configuration
    name = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=50,
        choices=Report.REPORT_TYPE_CHOICES
    )
    format = models.CharField(
        max_length=20,
        choices=Report.FORMAT_CHOICES,
        default='pdf'
    )
    
    # Recurrence
    frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES
    )
    day_of_week = models.IntegerField(
        null=True,
        blank=True,
        help_text="Day of week (0=Monday, 6=Sunday)"
    )
    day_of_month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Day of month (1-31)"
    )
    time_of_day = models.TimeField(
        default='09:00',
        help_text="Time to generate report"
    )
    
    # Recipients
    recipients = models.JSONField(
        default=list,
        help_text="Email addresses to send report to"
    )
    
    # Parameters
    parameters = models.JSONField(
        default=dict,
        help_text="Report generation parameters"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        'iam.AppUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='report_schedules_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'report_schedule'
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['next_run']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"