"""Response Serializers"""

from rest_framework import serializers
from .models import Response, ResponseReview, Evidence, EvidenceTag, ResponseEvidence


class ResponseSerializer(serializers.ModelSerializer):
    """Response serializer"""
    question_text = serializers.CharField(source='assessment_question.question_text', read_only=True)
    question_code = serializers.CharField(source='assessment_question.code', read_only=True)
    responder_name = serializers.CharField(source='responder_user.full_name', read_only=True)
    evidence_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Response
        fields = [
            'id', 'assessment', 'assessment_question', 'question_code', 'question_text',
            'answer_payload', 'maturity_score', 'responder_comments',
            'status', 'responder_user', 'responder_name',
            'submitted_at', 'approved_at', 'auto_populated',
            'evidence_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'maturity_score', 'submitted_at', 'approved_at', 'created_at', 'updated_at']
    
    def get_evidence_count(self, obj):
        return obj.evidence_links.count()


class ResponseReviewSerializer(serializers.ModelSerializer):
    """Review serializer"""
    reviewer_name = serializers.CharField(source='reviewer_user.full_name', read_only=True)
    
    class Meta:
        model = ResponseReview
        fields = ['id', 'response', 'reviewer_user', 'reviewer_name', 'decision', 'comments', 'reviewed_at']
        read_only_fields = ['id', 'reviewed_at']


class EvidenceTagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    class Meta:
        model = EvidenceTag
        fields = ['id', 'evidence', 'tag']
        read_only_fields = ['id']


class EvidenceSerializer(serializers.ModelSerializer):
    """Evidence serializer"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    tags = EvidenceTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Evidence
        fields = [
            'id', 'assessment', 'file_name', 'file_path', 'file_type',
            'file_size', 'mime_type', 'title', 'description', 'status',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'expires_at', 'tags'
        ]
        read_only_fields = ['id', 'uploaded_at']


class ResponseEvidenceSerializer(serializers.ModelSerializer):
    """Link serializer"""
    evidence_title = serializers.CharField(source='evidence.title', read_only=True)
    evidence_file_name = serializers.CharField(source='evidence.file_name', read_only=True)
    
    class Meta:
        model = ResponseEvidence
        fields = ['id', 'response', 'evidence', 'evidence_title', 'evidence_file_name', 'linked_at']
        read_only_fields = ['id', 'linked_at']