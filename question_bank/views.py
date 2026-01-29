"""
Question Bank Views - REST API Endpoints
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    QuestionBank, QuestionBankOption, ControlQuestionMap,
    QuestionApplicabilityRule
)
from .serializers import (
    QuestionBankSerializer, QuestionBankCreateSerializer,
    QuestionBankOptionSerializer, ControlQuestionMapSerializer,
    QuestionApplicabilityRuleSerializer
)
from iam.permissions import IsAuthenticated


class QuestionBankViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing question bank.
    GET /api/v1/questions/
    POST /api/v1/questions/
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['scale_type', 'question_type', 'is_active', 'pptdf_code']
    search_fields = ['code', 'question_text', 'guidance']
    ordering_fields = ['code', 'created_at']
    
    def get_queryset(self):
        return QuestionBank.objects.filter(
            tenant=self.request.user.tenant
        ).prefetch_related('options')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuestionBankCreateSerializer
        return QuestionBankSerializer
    
    @action(detail=True, methods=['get'])
    def controls(self, request, pk=None):
        """
        Get all controls mapped to this question.
        GET /api/v1/questions/{id}/controls/
        """
        question = self.get_object()
        mappings = question.control_mappings.select_related('control_node')
        serializer = ControlQuestionMapSerializer(mappings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a question.
        POST /api/v1/questions/{id}/duplicate/
        """
        original = self.get_object()
        
        # Create duplicate
        duplicate = QuestionBank.objects.create(
            tenant=original.tenant,
            code=f"{original.code}_copy",
            question_text=original.question_text,
            question_type=original.question_type,
            guidance=original.guidance,
            scale_type=original.scale_type,
            metadata=original.metadata,
            pptdf_code=original.pptdf_code,
            erl_refs=original.erl_refs,
            suggested_evidence_tags=original.suggested_evidence_tags
        )
        
        # Copy options
        for option in original.options.all():
            QuestionBankOption.objects.create(
                question_bank=duplicate,
                option_value=option.option_value,
                option_text=option.option_text,
                score_weight=option.score_weight,
                description=option.description,
                display_order=option.display_order
            )
        
        serializer = self.get_serializer(duplicate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuestionBankOptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing question options.
    GET /api/v1/question-options/
    """
    serializer_class = QuestionBankOptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question_bank']
    
    def get_queryset(self):
        return QuestionBankOption.objects.filter(
            question_bank__tenant=self.request.user.tenant
        )


class ControlQuestionMapViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing control-question mappings.
    GET /api/v1/control-question-maps/
    POST /api/v1/control-question-maps/
    """
    serializer_class = ControlQuestionMapSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['control_node', 'question_bank', 'is_mandatory']
    
    def get_queryset(self):
        return ControlQuestionMap.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('control_node', 'question_bank')
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create mappings.
        POST /api/v1/control-question-maps/bulk_create/
        Body: {"control_node_ids": [...], "question_bank_ids": [...]}
        """
        control_ids = request.data.get('control_node_ids', [])
        question_ids = request.data.get('question_bank_ids', [])
        
        created = []
        for control_id in control_ids:
            for question_id in question_ids:
                mapping, was_created = ControlQuestionMap.objects.get_or_create(
                    tenant=request.user.tenant,
                    control_node_id=control_id,
                    question_bank_id=question_id
                )
                if was_created:
                    created.append(mapping)
        
        serializer = self.get_serializer(created, many=True)
        return Response({
            'created': len(created),
            'mappings': serializer.data
        }, status=status.HTTP_201_CREATED)


class QuestionApplicabilityRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing applicability rules.
    GET /api/v1/question-rules/
    """
    serializer_class = QuestionApplicabilityRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question_bank', 'rule_type']
    
    def get_queryset(self):
        return QuestionApplicabilityRule.objects.filter(
            tenant=self.request.user.tenant
        )
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)