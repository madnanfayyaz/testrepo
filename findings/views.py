"""Findings Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    Finding, FindingSeverity, RemediationAction,
    RemediationTask, RiskAcceptance
)
from .serializers import (
    FindingSerializer, FindingSeveritySerializer,
    RemediationActionSerializer, RemediationTaskSerializer,
    RiskAcceptanceSerializer
)
from iam.permissions import IsAuthenticated


class FindingViewSet(viewsets.ModelViewSet):
    """Finding CRUD"""
    serializer_class = FindingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assessment', 'severity', 'status', 'assigned_to', 'control_node']
    search_fields = ['finding_number', 'title', 'description']
    ordering_fields = ['identified_date', 'severity', 'due_date']
    
    def get_queryset(self):
        return Finding.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        # Generate finding number
        from django.utils import timezone
        finding_count = Finding.objects.filter(tenant=self.request.user.tenant).count()
        finding_number = f"F-{timezone.now().year}-{finding_count + 1:04d}"
        
        serializer.save(
            tenant=self.request.user.tenant,
            finding_number=finding_number,
            identified_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark finding as resolved"""
        finding = self.get_object()
        finding.resolve(request.user)
        return Response({'message': 'Finding marked as resolved'})
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close finding"""
        finding = self.get_object()
        try:
            finding.close()
            return Response({'message': 'Finding closed'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def remediation_actions(self, request, pk=None):
        """Get all remediation actions for this finding"""
        finding = self.get_object()
        actions = finding.remediation_actions.all()
        serializer = RemediationActionSerializer(actions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue findings"""
        findings = [f for f in self.get_queryset() if f.is_overdue()]
        serializer = self.get_serializer(findings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_severity(self, request):
        """Get findings grouped by severity"""
        findings = self.get_queryset()
        result = {}
        for severity, _ in Finding.SEVERITY_CHOICES:
            result[severity] = findings.filter(severity=severity).count()
        return Response(result)


class FindingSeverityViewSet(viewsets.ModelViewSet):
    """Finding severity CRUD"""
    serializer_class = FindingSeveritySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FindingSeverity.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class RemediationActionViewSet(viewsets.ModelViewSet):
    """Remediation action CRUD"""
    serializer_class = RemediationActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['finding', 'status', 'priority', 'owner']
    ordering_fields = ['target_date', 'priority']
    
    def get_queryset(self):
        return RemediationAction.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for this action"""
        action = self.get_object()
        tasks = action.tasks.all()
        serializer = RemediationTaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark action as completed"""
        action = self.get_object()
        action.status = 'completed'
        action.completed_date = timezone.now().date()
        action.save()
        return Response({'message': 'Action marked as completed'})


class RemediationTaskViewSet(viewsets.ModelViewSet):
    """Remediation task CRUD"""
    serializer_class = RemediationTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['remediation_action', 'status', 'assigned_to']
    
    def get_queryset(self):
        return RemediationTask.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.complete()
        return Response({'message': 'Task marked as completed'})


class RiskAcceptanceViewSet(viewsets.ModelViewSet):
    """Risk acceptance CRUD"""
    serializer_class = RiskAcceptanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['finding', 'status']
    
    def get_queryset(self):
        return RiskAcceptance.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        from django.utils import timezone
        serializer.save(
            tenant=self.request.user.tenant,
            requested_by=self.request.user,
            requested_date=timezone.now().date()
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve risk acceptance"""
        acceptance = self.get_object()
        acceptance.approve(request.user)
        return Response({'message': 'Risk acceptance approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject risk acceptance"""
        acceptance = self.get_object()
        acceptance.reject()
        return Response({'message': 'Risk acceptance rejected'})