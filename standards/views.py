"""
Standards Views - REST API Endpoints
Provides: Standard browsing, control navigation, search, mappings
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Prefetch
from iam.permissions import IsAuthenticated

from .models import (
    Standard, StandardVersion, ControlNode, ControlNodeTag,
    ControlMapping, TenantControlExtension
)
from .serializers import (
    StandardSerializer, StandardVersionSerializer,
    ControlNodeListSerializer, ControlNodeDetailSerializer,
    ControlNodeTreeSerializer, ControlMappingSerializer,
    TenantControlExtensionSerializer, ControlSearchSerializer
)


class StandardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing standards.
    GET /api/v1/standards/
    POST /api/v1/standards/
    GET /api/v1/standards/{id}/
    """
    serializer_class = StandardSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['scope', 'code']
    search_fields = ['code', 'name', 'owner']
    ordering_fields = ['code', 'name']
    
    def get_queryset(self):
        """Filter by tenant - show global + tenant-specific"""
        user = self.request.user
        return Standard.objects.filter(
            Q(scope='global', tenant=user.tenant) |
            Q(scope='tenant', tenant=user.tenant)
        ).select_related('tenant').prefetch_related('versions')
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions of a standard.
        GET /api/v1/standards/{id}/versions/
        """
        standard = self.get_object()
        versions = standard.versions.all()
        serializer = StandardVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def latest(self, request, pk=None):
        """
        Get latest version of a standard.
        GET /api/v1/standards/{id}/latest/
        """
        standard = self.get_object()
        latest = standard.get_latest_version()
        if latest:
            serializer = StandardVersionSerializer(latest)
            return Response(serializer.data)
        return Response({
            'error': 'No versions found for this standard'
        }, status=status.HTTP_404_NOT_FOUND)


class StandardVersionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing standard versions.
    GET /api/v1/standard-versions/
    """
    serializer_class = StandardVersionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['standard', 'is_locked']
    search_fields = ['version_label', 'standard__code']
    ordering_fields = ['released_on', 'version_label']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        return StandardVersion.objects.filter(
            Q(standard__scope='global', standard__tenant=user.tenant) |
            Q(standard__scope='tenant', standard__tenant=user.tenant)
        ).select_related('standard')
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """
        Get full control tree for this version.
        GET /api/v1/standard-versions/{id}/tree/
        """
        version = self.get_object()
        root_nodes = version.get_root_nodes()
        serializer = ControlNodeTreeSerializer(root_nodes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def controls(self, request, pk=None):
        """
        Get all controls (flat list) for this version.
        GET /api/v1/standard-versions/{id}/controls/
        """
        version = self.get_object()
        controls = version.get_all_controls()
        serializer = ControlNodeListSerializer(controls, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Get statistics for this version.
        GET /api/v1/standard-versions/{id}/statistics/
        """
        version = self.get_object()
        
        stats = {
            'total_nodes': version.control_nodes.count(),
            'by_type': {},
            'by_status': {},
            'by_criticality': {
                'critical': version.control_nodes.filter(criticality_weight__gte=8).count(),
                'high': version.control_nodes.filter(
                    criticality_weight__gte=5, criticality_weight__lt=8
                ).count(),
                'medium': version.control_nodes.filter(
                    criticality_weight__gte=3, criticality_weight__lt=5
                ).count(),
                'low': version.control_nodes.filter(criticality_weight__lt=3).count(),
            }
        }
        
        # Count by node type
        type_counts = version.control_nodes.values('node_type').annotate(count=Count('id'))
        for item in type_counts:
            stats['by_type'][item['node_type']] = item['count']
        
        # Count by status
        status_counts = version.control_nodes.values('status').annotate(count=Count('id'))
        for item in status_counts:
            stats['by_status'][item['status']] = item['count']
        
        return Response(stats)


class ControlNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing control nodes.
    GET /api/v1/controls/
    GET /api/v1/controls/{id}/
    """
    permission_classes = [IsAuthenticated]
    filterset_fields = ['standard_version', 'node_type', 'status', 'parent']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['code', 'display_order', 'criticality_weight']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        return ControlNode.objects.filter(
            Q(standard_version__standard__scope='global', 
              standard_version__standard__tenant=user.tenant) |
            Q(standard_version__standard__scope='tenant', 
              standard_version__standard__tenant=user.tenant)
        ).select_related(
            'standard_version__standard', 'parent'
        ).prefetch_related('children', 'tags')
    
    def get_serializer_class(self):
        """Use detailed serializer for single object, list for multiple"""
        if self.action == 'retrieve':
            return ControlNodeDetailSerializer
        return ControlNodeListSerializer
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Get direct children of a control node.
        GET /api/v1/controls/{id}/children/
        """
        node = self.get_object()
        children = node.children.filter(status='active').order_by('display_order', 'code')
        serializer = ControlNodeListSerializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """
        Get all parent nodes up to root.
        GET /api/v1/controls/{id}/ancestors/
        """
        node = self.get_object()
        ancestors = node.get_ancestors()
        serializer = ControlNodeListSerializer(ancestors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """
        Get all child nodes recursively.
        GET /api/v1/controls/{id}/descendants/
        """
        node = self.get_object()
        descendants = node.get_descendants()
        serializer = ControlNodeListSerializer(descendants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """
        Add a tag to control node.
        POST /api/v1/controls/{id}/add_tag/
        Body: {"tag": "cloud"}
        """
        node = self.get_object()
        tag_name = request.data.get('tag')
        
        if not tag_name:
            return Response({
                'error': 'tag is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tag, created = ControlNodeTag.objects.get_or_create(
            tenant=request.user.tenant,
            node=node,
            tag=tag_name.lower()
        )
        
        return Response({
            'message': 'Tag added' if created else 'Tag already exists',
            'tag': tag.tag
        })
    
    @action(detail=True, methods=['post'])
    def remove_tag(self, request, pk=None):
        """
        Remove a tag from control node.
        POST /api/v1/controls/{id}/remove_tag/
        Body: {"tag": "cloud"}
        """
        node = self.get_object()
        tag_name = request.data.get('tag')
        
        if not tag_name:
            return Response({
                'error': 'tag is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count, _ = ControlNodeTag.objects.filter(
            tenant=request.user.tenant,
            node=node,
            tag=tag_name.lower()
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Tag removed'})
        return Response({
            'error': 'Tag not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced control search.
        GET /api/v1/controls/search/?q=encryption&type=control&standard=ISO_27001
        """
        query = request.query_params.get('q', '')
        node_type = request.query_params.get('type', None)
        standard_code = request.query_params.get('standard', None)
        
        if not query:
            return Response({
                'error': 'Query parameter "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        qs = self.get_queryset()
        
        # Text search
        qs = qs.filter(
            Q(code__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        
        # Filter by type
        if node_type:
            qs = qs.filter(node_type=node_type)
        
        # Filter by standard
        if standard_code:
            qs = qs.filter(standard_version__standard__code=standard_code)
        
        # Limit results
        qs = qs[:50]
        
        # Build search results
        results = []
        for node in qs:
            results.append({
                'id': str(node.id),
                'code': node.code,
                'title': node.title,
                'node_type': node.node_type,
                'standard_code': node.standard_version.standard.code,
                'standard_name': node.standard_version.standard.name,
                'version_label': node.standard_version.version_label,
                'hierarchy_path': node.get_hierarchy_path()
            })
        
        return Response({
            'query': query,
            'count': len(results),
            'results': results
        })


class ControlMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing control mappings.
    GET /api/v1/control-mappings/
    POST /api/v1/control-mappings/
    """
    serializer_class = ControlMappingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['source_node', 'target_node', 'mapping_type']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        return ControlMapping.objects.filter(
            tenant=user.tenant
        ).select_related(
            'source_node__standard_version__standard',
            'target_node__standard_version__standard'
        )
    
    def perform_create(self, serializer):
        """Set tenant on create"""
        serializer.save(tenant=self.request.user.tenant)
    
    @action(detail=False, methods=['get'])
    def by_standard(self, request):
        """
        Get mappings between two standards.
        GET /api/v1/control-mappings/by_standard/?source=ISO_27001&target=NIST_CSF
        """
        source_code = request.query_params.get('source')
        target_code = request.query_params.get('target')
        
        if not source_code or not target_code:
            return Response({
                'error': 'Both source and target parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        mappings = self.get_queryset().filter(
            source_node__standard_version__standard__code=source_code,
            target_node__standard_version__standard__code=target_code
        )
        
        serializer = self.get_serializer(mappings, many=True)
        return Response({
            'source_standard': source_code,
            'target_standard': target_code,
            'mapping_count': mappings.count(),
            'mappings': serializer.data
        })


class TenantControlExtensionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tenant custom controls.
    GET /api/v1/custom-controls/
    POST /api/v1/custom-controls/
    """
    serializer_class = TenantControlExtensionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'base_node']
    search_fields = ['custom_code', 'title', 'description']
    ordering_fields = ['custom_code', 'created_at']
    
    def get_queryset(self):
        """Filter by tenant"""
        user = self.request.user
        return TenantControlExtension.objects.filter(
            tenant=user.tenant
        ).select_related('base_node', 'owner_user')
    
    def perform_create(self, serializer):
        """Set tenant and owner on create"""
        serializer.save(
            tenant=self.request.user.tenant,
            owner_user=self.request.user
        )
