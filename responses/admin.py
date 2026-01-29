"""Response Admin"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Response, ResponseVersion, ResponseReview,
    Evidence, EvidenceTag, ResponseEvidence
)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = [
        'assessment_question', 'maturity_score_display', 'status',
        'responder_user', 'submitted_at', 'evidence_count'
    ]
    list_filter = ['status', 'assessment']
    search_fields = ['assessment_question__code', 'responder_comments']
    readonly_fields = ['id', 'maturity_score', 'submitted_at', 'approved_at', 'created_at']
    
    fieldsets = (
        ('Question', {
            'fields': ('id', 'assessment', 'assessment_question')
        }),
        ('Answer', {
            'fields': ('answer_payload', 'maturity_score', 'responder_comments')
        }),
        ('Workflow', {
            'fields': ('status', 'responder_user', 'submitted_at', 'approved_at', 'approved_by', 'reviewer_comments')
        }),
        ('Metadata', {
            'fields': ('auto_populated', 'source_response_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def maturity_score_display(self, obj):
        if obj.maturity_score:
            color = 'green' if obj.maturity_score >= 4 else 'orange' if obj.maturity_score >= 3 else 'red'
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.maturity_score)
        return '-'
    maturity_score_display.short_description = 'Score'
    
    def evidence_count(self, obj):
        count = obj.evidence_links.count()
        return format_html('<span style="color: blue;">{} files</span>', count)
    evidence_count.short_description = 'Evidence'


@admin.register(ResponseReview)
class ResponseReviewAdmin(admin.ModelAdmin):
    list_display = ['response', 'reviewer_user', 'decision', 'reviewed_at']
    list_filter = ['decision']
    search_fields = ['response__assessment_question__code', 'comments']


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'file_name', 'file_type', 'file_size_display',
        'status', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['file_type', 'status', 'assessment']
    search_fields = ['title', 'file_name', 'description']
    readonly_fields = ['uploaded_at']
    
    def file_size_display(self, obj):
        size_kb = obj.file_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        return f"{size_kb/1024:.1f} MB"
    file_size_display.short_description = 'Size'


@admin.register(EvidenceTag)
class EvidenceTagAdmin(admin.ModelAdmin):
    list_display = ['evidence', 'tag']
    list_filter = ['tag']
    search_fields = ['evidence__title', 'tag']


@admin.register(ResponseEvidence)
class ResponseEvidenceAdmin(admin.ModelAdmin):
    list_display = ['response', 'evidence', 'linked_at', 'linked_by']
    list_filter = ['linked_at']
    search_fields = ['response__assessment_question__code', 'evidence__title']