"""Reporting Serializers"""

from rest_framework import serializers
from .models import Dashboard, DashboardWidget, Report, ReportSchedule


class DashboardWidgetSerializer(serializers.ModelSerializer):
    """Dashboard widget serializer"""
    
    class Meta:
        model = DashboardWidget
        fields = [
            'id', 'dashboard', 'title', 'widget_type', 'data_source',
            'query_config', 'chart_config', 'position_x', 'position_y',
            'width', 'height', 'show_legend', 'show_title',
            'cache_duration', 'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardSerializer(serializers.ModelSerializer):
    """Dashboard serializer"""
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    widget_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'dashboard_type',
            'created_by', 'created_by_name', 'is_default', 'is_shared',
            'layout_config', 'auto_refresh', 'refresh_interval',
            'widgets', 'widget_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_widget_count(self, obj):
        return obj.widgets.count()


class ReportSerializer(serializers.ModelSerializer):
    """Report serializer"""
    generated_by_name = serializers.CharField(source='generated_by.full_name', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'report_type', 'format', 'description',
            'assessment', 'parameters', 'status', 'file_path',
            'file_size', 'file_size_display', 'generated_by',
            'generated_by_name', 'generated_at', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'file_path', 'file_size', 'generated_at', 'created_at', 'updated_at']
    
    def get_file_size_display(self, obj):
        if not obj.file_size:
            return None
        size_kb = obj.file_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        return f"{size_kb/1024:.1f} MB"


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Report schedule serializer"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'format', 'frequency',
            'day_of_week', 'day_of_month', 'time_of_day',
            'recipients', 'parameters', 'is_active', 'last_run',
            'next_run', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']