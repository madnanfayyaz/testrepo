"""Reporting Admin"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Dashboard, DashboardWidget, Report, ReportSchedule


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'dashboard_type', 'created_by',
        'is_default', 'is_shared', 'widget_count', 'created_at'
    ]
    list_filter = ['dashboard_type', 'is_default', 'is_shared']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Dashboard Info', {
            'fields': ('name', 'description', 'dashboard_type')
        }),
        ('Ownership & Sharing', {
            'fields': ('created_by', 'is_default', 'is_shared')
        }),
        ('Configuration', {
            'fields': ('layout_config', 'auto_refresh', 'refresh_interval')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def widget_count(self, obj):
        count = obj.widgets.count()
        return format_html('<span style="color: blue;">{} widgets</span>', count)
    widget_count.short_description = 'Widgets'


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'dashboard', 'widget_type', 'data_source',
        'position_display', 'size_display', 'display_order'
    ]
    list_filter = ['widget_type', 'data_source']
    search_fields = ['title', 'dashboard__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def position_display(self, obj):
        return f"({obj.position_x}, {obj.position_y})"
    position_display.short_description = 'Position'
    
    def size_display(self, obj):
        return f"{obj.width}x{obj.height}"
    size_display.short_description = 'Size'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'format', 'status_display',
        'generated_by', 'generated_at', 'file_size_display'
    ]
    list_filter = ['report_type', 'format', 'status']
    search_fields = ['name', 'description']
    readonly_fields = ['status', 'file_path', 'file_size', 'generated_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Report Details', {
            'fields': ('name', 'description', 'report_type', 'format')
        }),
        ('Scope', {
            'fields': ('assessment', 'parameters')
        }),
        ('Generation', {
            'fields': ('status', 'file_path', 'file_size', 'generated_by', 'generated_at')
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'pending': 'gray',
            'generating': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def file_size_display(self, obj):
        if not obj.file_size:
            return '-'
        size_kb = obj.file_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        return f"{size_kb/1024:.1f} MB"
    file_size_display.short_description = 'File Size'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'frequency', 'is_active',
        'last_run', 'next_run', 'recipient_count'
    ]
    list_filter = ['frequency', 'is_active', 'report_type']
    search_fields = ['name']
    readonly_fields = ['last_run', 'next_run', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Schedule Info', {
            'fields': ('name', 'report_type', 'format')
        }),
        ('Recurrence', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'time_of_day')
        }),
        ('Recipients', {
            'fields': ('recipients',)
        }),
        ('Parameters', {
            'fields': ('parameters',)
        }),
        ('Status', {
            'fields': ('is_active', 'last_run', 'next_run')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def recipient_count(self, obj):
        count = len(obj.recipients) if obj.recipients else 0
        return f"{count} recipients"
    recipient_count.short_description = 'Recipients'