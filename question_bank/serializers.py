"""
Question Bank Serializers - DRF Serializers
"""

from rest_framework import serializers
from .models import (
    QuestionBank, QuestionBankOption, ControlQuestionMap,
    QuestionApplicabilityRule
)


class QuestionBankOptionSerializer(serializers.ModelSerializer):
    """Serializer for question options"""
    
    class Meta:
        model = QuestionBankOption
        fields = [
            'id', 'option_value', 'option_text', 'score_weight',
            'description', 'display_order'
        ]
        read_only_fields = ['id']


class QuestionBankSerializer(serializers.ModelSerializer):
    """Serializer for QuestionBank with options"""
    options = QuestionBankOptionSerializer(many=True, read_only=True)
    control_count = serializers.IntegerField(source='get_control_count', read_only=True)
    usage_count = serializers.IntegerField(source='get_assessment_usage_count', read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'tenant', 'code', 'question_text', 'question_type',
            'guidance', 'scale_type', 'metadata', 'pptdf_code',
            'erl_refs', 'suggested_evidence_tags', 'is_active',
            'options', 'control_count', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionBankCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating questions with auto-generated options"""
    auto_create_options = serializers.BooleanField(
        write_only=True,
        default=True,
        help_text="Auto-create Likert scale options"
    )
    
    class Meta:
        model = QuestionBank
        fields = [
            'code', 'question_text', 'question_type', 'guidance',
            'scale_type', 'metadata', 'pptdf_code', 'erl_refs',
            'suggested_evidence_tags', 'auto_create_options'
        ]
    
    def create(self, validated_data):
        auto_create = validated_data.pop('auto_create_options', True)
        tenant = self.context['request'].user.tenant
        
        question = QuestionBank.objects.create(
            tenant=tenant,
            **validated_data
        )
        
        # Auto-create options
        if auto_create:
            if question.scale_type == 'LIKERT_1_5':
                from .models import create_default_likert_options
                create_default_likert_options(question)
            elif question.scale_type == 'YES_NO':
                from .models import create_yes_no_options
                create_yes_no_options(question)
        
        return question


class ControlQuestionMapSerializer(serializers.ModelSerializer):
    """Serializer for control-question mappings"""
    control_code = serializers.CharField(source='control_node.code', read_only=True)
    control_title = serializers.CharField(source='control_node.title', read_only=True)
    question_code = serializers.CharField(source='question_bank.code', read_only=True)
    question_text = serializers.CharField(source='question_bank.question_text', read_only=True)
    
    class Meta:
        model = ControlQuestionMap
        fields = [
            'id', 'tenant', 'control_node', 'control_code', 'control_title',
            'question_bank', 'question_code', 'question_text',
            'is_mandatory', 'guidance', 'pptdf_code', 'erl_refs',
            'suggested_evidence_tags', 'display_order'
        ]
        read_only_fields = ['id']


class QuestionApplicabilityRuleSerializer(serializers.ModelSerializer):
    """Serializer for applicability rules"""
    
    class Meta:
        model = QuestionApplicabilityRule
        fields = [
            'id', 'tenant', 'question_bank', 'rule_type',
            'depends_on_question', 'operator', 'value_text',
            'value_numeric'
        ]
        read_only_fields = ['id']