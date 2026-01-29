"""Reporting Views"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Dashboard, DashboardWidget, Report, ReportSchedule
from .serializers import (
    DashboardSerializer, DashboardWidgetSerializer,
    ReportSerializer, ReportScheduleSerializer
)
from .utils import get_metrics_data
from iam.permissions import IsAuthenticated


class DashboardViewSet(viewsets.ModelViewSet):
    """Dashboard CRUD"""
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['dashboard_type', 'is_default', 'is_shared', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        return Dashboard.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Get dashboard data for all widgets"""
        dashboard = self.get_object()
        widget_data = {}
        
        for widget in dashboard.widgets.all():
            widget_data[str(widget.id)] = get_metrics_data(
                tenant=request.user.tenant,
                data_source=widget.data_source,
                config=widget.query_config
            )
        
        return Response({
            'dashboard_id': str(dashboard.id),
            'dashboard_name': dashboard.name,
            'widgets': widget_data
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set as default dashboard"""
        dashboard = self.get_object()
        
        # Clear other defaults
        Dashboard.objects.filter(
            tenant=dashboard.tenant,
            is_default=True
        ).update(is_default=False)
        
        dashboard.is_default = True
        dashboard.save()
        
        return Response({'message': 'Dashboard set as default'})


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """Dashboard widget CRUD"""
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['dashboard', 'widget_type', 'data_source']
    
    def get_queryset(self):
        return DashboardWidget.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['get'])
    def refresh(self, request, pk=None):
        """Refresh widget data (clear cache)"""
        widget = self.get_object()
        widget.cached_data = None
        widget.last_cached = None
        widget.save()
        
        # Get fresh data
        data = get_metrics_data(
            tenant=request.user.tenant,
            data_source=widget.data_source,
            config=widget.query_config
        )
        
        return Response(data)


class ReportViewSet(viewsets.ModelViewSet):
    """Report CRUD"""
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'format', 'status', 'assessment', 'generated_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'generated_at']
    
    def get_queryset(self):
        return Report.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            generated_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Trigger report generation"""
        report = self.get_object()
        
        # Mark as generating
        report.mark_as_generating()
        
        # In production, this would queue a background job (Celery)
        # For now, simulate completion
        try:
            # Simulate generation
            file_path = f'/reports/{report.id}.{report.format}'
            file_size = 1024000  # Placeholder size
            
            report.mark_as_completed(file_path, file_size)
            
            return Response({
                'message': 'Report generation completed',
                'report_id': str(report.id),
                'status': report.status
            })
        except Exception as e:
            report.mark_as_failed(str(e))
            return Response({
                'error': 'Report generation failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download generated report"""
        report = self.get_object()
        
        if report.status != 'completed':
            return Response(
                {'error': 'Report not ready', 'status': report.status},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'download_url': report.file_path,
            'file_size': report.file_size,
            'format': report.format,
            'name': report.name
        })


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """Report schedule CRUD"""
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_active', 'frequency', 'report_type']
    ordering_fields = ['name', 'next_run']
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )


class MetricsViewSet(viewsets.ViewSet):
    """
    Metrics API endpoints for dashboards.
    Read-only endpoints providing various metrics.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get compliance overview"""
        from .utils import get_compliance_overview
        data = get_compliance_overview(request.user.tenant)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def assessments(self, request):
        """Get assessment metrics"""
        from .utils import get_assessment_metrics
        assessment_id = request.query_params.get('assessment_id')
        data = get_assessment_metrics(request.user.tenant, assessment_id)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def findings(self, request):
        """Get findings metrics"""
        from .utils import get_findings_metrics
        assessment_id = request.query_params.get('assessment_id')
        data = get_findings_metrics(request.user.tenant, assessment_id)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def maturity(self, request):
        """Get maturity metrics"""
        from .utils import get_maturity_metrics
        assessment_id = request.query_params.get('assessment_id')
        data = get_maturity_metrics(request.user.tenant, assessment_id)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def remediation(self, request):
        """Get remediation metrics"""
        from .utils import get_remediation_metrics
        data = get_remediation_metrics(request.user.tenant)
        return Response(data)