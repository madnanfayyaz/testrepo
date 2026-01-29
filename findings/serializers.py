"""Findings Serializers"""

from rest_framework import serializers
from .models import (
    Finding, FindingSeverity, FindingStatus,
    RemediationAction, RemediationTask, RiskAcceptance
)


class FindingSerializer(serializers.ModelSerializer):
    """Finding serializer"""
    control_code = serializers.CharField(source='control_node.code', read_only=True)
    control_title = serializers.CharField(source='control_node.title', read_only=True)
    identified_by_name = serializers.CharField(source='identified_by.full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    is_overdue = serializers.BooleanField(source='is_overdue', read_only=True)
    remediation_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Finding
        fields = [
            'id', 'assessment', 'response', 'control_node', 'control_code', 'control_title',
            'finding_number', 'title', 'description', 'severity', 'status',
            'impact', 'recommendation', 'identified_by', 'identified_by_name',
            'assigned_to', 'assigned_to_name', 'identified_date', 'due_date',
            'resolved_date', 'closed_date', 'auto_generated', 'is_overdue',
            'remediation_progress', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'finding_number', 'auto_generated', 'created_at', 'updated_at']
    
    def get_remediation_progress(self, obj):
        from .models import calculate_remediation_progress
        return calculate_remediation_progress(obj)


class FindingSeveritySerializer(serializers.ModelSerializer):
    """Finding severity serializer"""
    class Meta:
        model = FindingSeverity
        fields = ['id', 'name', 'score_threshold', 'color', 'description', 'sla_days']
        read_only_fields = ['id']


class FindingStatusSerializer(serializers.ModelSerializer):
    """Finding status serializer"""
    class Meta:
        model = FindingStatus
        fields = ['id', 'name', 'description', 'is_final', 'color', 'display_order']
        read_only_fields = ['id']


class RemediationTaskSerializer(serializers.ModelSerializer):
    """Remediation task serializer"""
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    
    class Meta:
        model = RemediationTask
        fields = [
            'id', 'remediation_action', 'title', 'description', 'status',
            'assigned_to', 'assigned_to_name', 'due_date', 'completed_date',
            'display_order', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RemediationActionSerializer(serializers.ModelSerializer):
    """Remediation action serializer"""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    progress_percentage = serializers.FloatField(source='get_progress_percentage', read_only=True)
    is_overdue = serializers.BooleanField(source='is_overdue', read_only=True)
    tasks = RemediationTaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = RemediationAction
        fields = [
            'id', 'finding', 'title', 'description', 'priority', 'status',
            'owner', 'owner_name', 'start_date', 'target_date', 'completed_date',
            'estimated_cost', 'actual_cost', 'progress_percentage', 'is_overdue',
            'tasks', 'task_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        return obj.tasks.count()


class RiskAcceptanceSerializer(serializers.ModelSerializer):
    """Risk acceptance serializer"""
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    is_expired = serializers.BooleanField(source='is_expired', read_only=True)
    
    class Meta:
        model = RiskAcceptance
        fields = [
            'id', 'finding', 'justification', 'compensating_controls',
            'status', 'requested_by', 'requested_by_name', 'approved_by',
            'approved_by_name', 'requested_date', 'approved_date', 'expiry_date',
            'is_expired', 'created_at'
        ]
        read_only_fields = ['id', 'approved_by', 'approved_date', 'created_at']