"""Assessment Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Assessment, AssessmentScope, AssessmentQuestion, Assignment
from .serializers import (
    AssessmentSerializer, AssessmentScopeSerializer,
    AssessmentQuestionSerializer, AssignmentSerializer
)
from .materialization import materialize_assessment_questions
from iam.permissions import IsAuthenticated


class AssessmentViewSet(viewsets.ModelViewSet):
    """Assessment CRUD"""
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'owner_user', 'organization']
    search_fields = ['code', 'name']
    ordering_fields = ['created_at', 'due_date']
    
    def get_queryset(self):
        return Assessment.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            owner_user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def generate_questions(self, request, pk=None):
        """Materialize questions from control-question mappings"""
        assessment = self.get_object()
        result = materialize_assessment_questions(assessment)
        
        return Response({
            'message': 'Questions generated successfully',
            'created': result['created'],
            'total': result['total']
        })
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get all questions for this assessment"""
        assessment = self.get_object()
        questions = assessment.questions.all()
        serializer = AssessmentQuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get assessment progress summary"""
        assessment = self.get_object()
        total = assessment.questions.count()
        answered = assessment.questions.filter(responses__isnull=False).distinct().count()
        
        return Response({
            'total_questions': total,
            'answered': answered,
            'remaining': total - answered,
            'percentage': assessment.get_progress_percentage()
        })


class AssessmentScopeViewSet(viewsets.ModelViewSet):
    """Assessment scope CRUD"""
    serializer_class = AssessmentScopeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['assessment']
    
    def get_queryset(self):
        return AssessmentScope.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class AssessmentQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """Assessment questions (read-only)"""
    serializer_class = AssessmentQuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['assessment', 'is_mandatory']
    search_fields = ['code', 'question_text']
    
    def get_queryset(self):
        return AssessmentQuestion.objects.filter(tenant=self.request.user.tenant)


class AssignmentViewSet(viewsets.ModelViewSet):
    """Assignment CRUD"""
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['assessment', 'assigned_to_user', 'assigned_to_bu', 'status']
    
    def get_queryset(self):
        return Assignment.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            assigned_by=self.request.user
        )