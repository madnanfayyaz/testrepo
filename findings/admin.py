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
        'owner_display', 'target_date_display', 'progress'
    ]
    list_filter = ['priority', 'status']
    search_fields = ['title', 'description']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def progress(self, obj):
        pct = obj.get_progress_percentage()
        color = 'green' if pct >= 75 else 'orange' if pct >= 50 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, pct)
    progress.short_description = 'Progress'
    
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
        'finding', 'status', 'requested_by',
        'approved_by', 'requested_date', 'expiry_date'
    ]
    list_filter = ['status']
    readonly_fields = ['requested_date', 'approved_date']
