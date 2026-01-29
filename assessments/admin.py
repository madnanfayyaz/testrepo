"""Assessment Admin"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Assessment, AssessmentScope, AssessmentQuestion, Assignment
)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'owner_user', 'due_date', 'progress_display', 'is_overdue']
    list_filter = ['status', 'owner_user']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def progress_display(self, obj):
        pct = obj.get_progress_percentage()
        color = 'green' if pct >= 75 else 'orange' if pct >= 50 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, pct)
    progress_display.short_description = 'Progress'


@admin.register(AssessmentScope)
class AssessmentScopeAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'control_node', 'include_children']
    list_filter = ['assessment']


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_code', 'assessment', 'question_short', 'is_mandatory']
    list_filter = ['assessment', 'is_mandatory']
    search_fields = ['question_code', 'question_text']
    
    def question_short(self, obj):
        return obj.question_text[:60] + '...'
    question_short.short_description = 'Question'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_display', 'assignee', 'status', 'due_date']
    list_filter = ['status']
    search_fields = ['assessment_question__question_code', 'assigned_to__username']
    
    def assessment_display(self, obj):
        return obj.assessment_question.assessment
    assessment_display.short_description = 'Assessment'
    
    def assignee(self, obj):
        return obj.assigned_to
    assignee.short_description = 'Assigned To'
