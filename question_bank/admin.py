"""
Question Bank Admin - Enhanced Admin Interface
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    QuestionBank, QuestionBankOption, ControlQuestionMap,
    QuestionApplicabilityRule
)


class QuestionBankOptionInline(admin.TabularInline):
    model = QuestionBankOption
    extra = 0
    fields = ['option_value', 'option_text', 'score_weight', 'display_order']


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'question_text_short', 'question_type', 'scale_type',
        'pptdf_code', 'is_active', 'control_count', 'option_count'
    ]
    list_filter = ['question_type', 'scale_type', 'is_active', 'pptdf_code']
    search_fields = ['code', 'question_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [QuestionBankOptionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'code', 'question_text')
        }),
        ('Configuration', {
            'fields': ('question_type', 'scale_type', 'guidance', 'is_active')
        }),
        ('Compliance Attributes', {
            'fields': ('pptdf_code', 'erl_refs', 'suggested_evidence_tags'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    question_text_short.short_description = 'Question'
    
    def control_count(self, obj):
        count = obj.get_control_count()
        return format_html('<span style="color: blue;">{} controls</span>', count)
    control_count.short_description = 'Mapped to'
    
    def option_count(self, obj):
        return obj.options.count()
    option_count.short_description = 'Options'


@admin.register(QuestionBankOption)
class QuestionBankOptionAdmin(admin.ModelAdmin):
    list_display = ['question_bank', 'option_value', 'option_text', 'score_weight']
    list_filter = ['question_bank__scale_type']
    search_fields = ['question_bank__code', 'option_text']


@admin.register(ControlQuestionMap)
class ControlQuestionMapAdmin(admin.ModelAdmin):
    list_display = [
        'control_code', 'question_code', 'rationale_short'
    ]
    list_filter = ['tenant']
    search_fields = [
        'control_node__code', 'control_node__title',
        'question_bank__code', 'question_bank__question_text'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Mapping', {
            'fields': ('tenant', 'control_node', 'question_bank')
        }),
        ('Configuration', {
            'fields': ('rationale', 'criticality_override')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def control_code(self, obj):
        return obj.control_node.code
    control_code.short_description = 'Control'
    
    def question_code(self, obj):
        return obj.question_bank.code
    question_code.short_description = 'Question'
    
    def rationale_short(self, obj):
        if obj.rationale:
            return obj.rationale[:50] + '...' if len(obj.rationale) > 50 else obj.rationale
        return '-'
    rationale_short.short_description = 'Rationale'

@admin.register(QuestionApplicabilityRule)
class QuestionApplicabilityRuleAdmin(admin.ModelAdmin):
    list_display = [
        'question_bank', 'rule_type', 'rule_value', 'is_required'
    ]
    list_filter = ['rule_type', 'is_required']
    search_fields = ['question_bank__code', 'rule_value']
