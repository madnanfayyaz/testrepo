"""Response Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Response, ResponseReview, Evidence, EvidenceTag, ResponseEvidence
from .serializers import (
    ResponseSerializer, ResponseReviewSerializer,
    EvidenceSerializer, EvidenceTagSerializer, ResponseEvidenceSerializer
)
from .utils import get_suggested_response
from iam.permissions import IsAuthenticated


class ResponseViewSet(viewsets.ModelViewSet):
    """Response CRUD with auto-population"""
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['assessment', 'assessment_question', 'status', 'responder_user']
    search_fields = ['responder_comments', 'reviewer_comments']
    
    def get_queryset(self):
        return Response.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            responder_user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit response for review"""
        response = self.get_object()
        try:
            response.submit()
            return DRFResponse({'message': 'Response submitted successfully'})
        except Exception as e:
            return DRFResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve response"""
        response = self.get_object()
        response.approve(request.user)
        return DRFResponse({'message': 'Response approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject response"""
        response = self.get_object()
        comments = request.data.get('comments', '')
        response.reject(comments)
        return DRFResponse({'message': 'Response rejected'})
    
    @action(detail=True, methods=['get'])
    def suggestion(self, request, pk=None):
        """Get auto-population suggestion"""
        response = self.get_object()
        suggestion = get_suggested_response(
            request.user.tenant,
            response.assessment_question.question_bank_id
        )
        if suggestion:
            return DRFResponse(suggestion)
        return DRFResponse({'message': 'No previous response found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def evidence(self, request, pk=None):
        """Get linked evidence"""
        response = self.get_object()
        links = response.evidence_links.all()
        serializer = ResponseEvidenceSerializer(links, many=True)
        return DRFResponse(serializer.data)


class ResponseReviewViewSet(viewsets.ModelViewSet):
    """Review CRUD"""
    serializer_class = ResponseReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['response', 'reviewer_user', 'decision']
    
    def get_queryset(self):
        return ResponseReview.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            reviewer_user=self.request.user
        )


class EvidenceViewSet(viewsets.ModelViewSet):
    """Evidence CRUD with file upload"""
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['assessment', 'file_type', 'status', 'uploaded_by']
    search_fields = ['title', 'description', 'file_name']
    
    def get_queryset(self):
        return Evidence.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            uploaded_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """Add tag to evidence"""
        evidence = self.get_object()
        tag_value = request.data.get('tag')
        if not tag_value:
            return DRFResponse({'error': 'Tag required'}, status=status.HTTP_400_BAD_REQUEST)
        
        EvidenceTag.objects.get_or_create(
            tenant=request.user.tenant,
            evidence=evidence,
            tag=tag_value
        )
        return DRFResponse({'message': f'Tag "{tag_value}" added'})
    
    @action(detail=True, methods=['delete'])
    def remove_tag(self, request, pk=None):
        """Remove tag from evidence"""
        evidence = self.get_object()
        tag_value = request.data.get('tag')
        EvidenceTag.objects.filter(
            tenant=request.user.tenant,
            evidence=evidence,
            tag=tag_value
        ).delete()
        return DRFResponse({'message': f'Tag "{tag_value}" removed'})


class ResponseEvidenceViewSet(viewsets.ModelViewSet):
    """Link responses to evidence"""
    serializer_class = ResponseEvidenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['response', 'evidence']
    
    def get_queryset(self):
        return ResponseEvidence.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            linked_by=self.request.user
        )