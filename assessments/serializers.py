"""Assessment Serializers"""

from rest_framework import serializers
from .models import (
    Assessment, AssessmentScope, AssessmentEntityScope,
    AssessmentQuestion, Assignment
)


class AssessmentSerializer(serializers.ModelSerializer):
    """Assessment serializer"""
    standard_code = serializers.CharField(source='standard_version.standard.code', read_only=True)
    version_label = serializers.CharField(source='standard_version.version_label', read_only=True)
    owner_name = serializers.CharField(source='owner_user.full_name', read_only=True)
    progress_percentage = serializers.FloatField(source='get_progress_percentage', read_only=True)
    is_overdue = serializers.BooleanField(source='is_overdue', read_only=True)
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'code', 'name', 'description', 'standard_version',
            'standard_code', 'version_label', 'owner_user', 'owner_name',
            'organization', 'status', 'start_date', 'due_date',
            'completed_at', 'progress_percentage', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class AssessmentScopeSerializer(serializers.ModelSerializer):
    """Assessment scope serializer"""
    control_code = serializers.CharField(source='control_node.code', read_only=True)
    control_title = serializers.CharField(source='control_node.title', read_only=True)
    
    class Meta:
        model = AssessmentScope
        fields = [
            'id', 'assessment', 'control_node', 'control_code',
            'control_title', 'include_children'
        ]
        read_only_fields = ['id']


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    """Materialized question serializer"""
    control_code = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentQuestion
        fields = [
            'id', 'assessment', 'node_id', 'control_code', 'code',
            'question_text', 'guidance', 'scale_type',
            'pptdf_code', 'erl_refs', 'suggested_evidence_tags',
            'is_mandatory', 'display_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_control_code(self, obj):
        control = obj.get_control_node()
        return control.code if control else None


class AssignmentSerializer(serializers.ModelSerializer):
    """Assignment serializer"""
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'assessment', 'assigned_to_user', 'assigned_to_bu',
            'assigned_to_name', 'assigned_by', 'assigned_by_name',
            'control_node', 'status', 'due_date', 'assigned_at',
            'completed_at', 'notes'
        ]
        read_only_fields = ['id', 'assigned_at', 'completed_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to_user:
            return obj.assigned_to_user.full_name
        elif obj.assigned_to_bu:
            return obj.assigned_to_bu.name
        return None