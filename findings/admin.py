"""Findings Admin"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Finding, FindingSeverity, RemediationAction,
    RemediationTask, RiskAcceptance
)


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = [
        'finding_number', 'title_short', 'severity_display',
        'status', 'assigned_to_display', 'due_date', 'overdue_display'
    ]
    list_filter = ['severity', 'status', 'assessment']
    search_fields = ['finding_number', 'title', 'description']
    readonly_fields = ['finding_number', 'auto_generated', 'created_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('finding_number', 'assessment', 'response', 'control_node')
        }),
        ('Details', {
            'fields': ('title', 'description', 'severity', 'status')
        }),
        ('Impact & Recommendation', {
            'fields': ('impact', 'recommendation')
        }),
        ('Ownership', {
            'fields': ('identified_by', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('identified_date', 'due_date', 'resolved_date', 'closed_date')
        }),
        ('Metadata', {
            'fields': ('auto_generated', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Title'
    
    def severity_display(self, obj):
        colors = {
            'critical': 'red',
            'high': 'orange',
            'medium': 'blue',
            'low': 'green',
            'informational': 'gray'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_display.short_description = 'Severity'
    
    def overdue_display(self, obj):
        if obj.is_overdue():
            return format_html('<span style="color: red;">⚠ OVERDUE</span>')
        return '-'
    overdue_display.short_description = 'Status'
 
    def assigned_to_display(self, obj):
        if obj.assigned_to:
            return obj.assigned_to
        return '-'
    assigned_to_display.short_description = 'Assigned To'

@admin.register(RemediationAction)
class RemediationActionAdmin(admin.ModelAdmin):
    list_display = [
        'finding', 'title_short', 'priority_display', 'status',
        'owner_display', 'target_date_display', 'progress_display'
    ]
    list_filter = ['status']
    search_fields = ['title', 'description']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def priority_display(self, obj):
        return obj.priority if hasattr(obj, 'priority') else '-'
    priority_display.short_description = 'Priority'
    
    def owner_display(self, obj):
        return obj.owner if hasattr(obj, 'owner') else '-'
    owner_display.short_description = 'Owner'
    
    def target_date_display(self, obj):
        return obj.target_date if hasattr(obj, 'target_date') else '-'
    target_date_display.short_description = 'Target Date'
    
    def progress_display(self, obj):
        if hasattr(obj, 'get_progress_percentage'):
            pct = obj.get_progress_percentage()
            color = 'green' if pct >= 75 else 'orange' if pct >= 50 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, pct)
        return '-'
    progress_display.short_description = 'Progress'
    
    def priority_display(self, obj):
        if obj.priority:
            return obj.priority
        return '-'
    priority_display.short_description = 'Priority'

    def owner_display(self, obj):
        if obj.owner:
            return obj.owner
        return '-'
    owner_display.short_description = 'Owner'

    def target_date_display(self, obj):
        if obj.target_date:
            return obj.target_date
        return '-'
    target_date_display.short_description = 'Target Date'

@admin.register(RemediationTask)
class RemediationTaskAdmin(admin.ModelAdmin):
    list_display = [
        'remediation_action', 'title', 'status',
        'assigned_to', 'due_date', 'completed_date'
    ]
    list_filter = ['status']
    search_fields = ['title', 'description']


@admin.register(RiskAcceptance)
class RiskAcceptanceAdmin(admin.ModelAdmin):
    list_display = [
        'finding', 'status_display', 'requested_by_display',
        'approved_by_display', 'requested_date_display', 'expiry_date_display'
    ]
    list_filter = ['status'] if hasattr(RiskAcceptance, 'status') else []
    readonly_fields = ['requested_date', 'approved_date'] if hasattr(RiskAcceptance, 'requested_date') else []
    
    def status_display(self, obj):
        return obj.status if hasattr(obj, 'status') else '-'
    status_display.short_description = 'Status'
    
    def requested_by_display(self, obj):
        return obj.requested_by if hasattr(obj, 'requested_by') else '-'
    requested_by_display.short_description = 'Requested By'
    
    def approved_by_display(self, obj):
        return obj.approved_by if hasattr(obj, 'approved_by') else '-'
    approved_by_display.short_description = 'Approved By'
    
    def requested_date_display(self, obj):
        return obj.requested_date if hasattr(obj, 'requested_date') else '-'
    requested_date_display.short_description = 'Requested Date'
    
    def expiry_date_display(self, obj):
        return obj.expiry_date if hasattr(obj, 'expiry_date') else '-'
    expiry_date_display.short_description = 'Expiry Date'
