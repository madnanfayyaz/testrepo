"""
Standards Serializers - DRF Serializers for Standards API
Complete version with all required serializers
"""

from rest_framework import serializers
from .models import (
    Standard, StandardVersion, ControlNode, ControlNodeTag,
    ControlMapping, TenantControlExtension
)


class StandardSerializer(serializers.ModelSerializer):
    """Serializer for Standard model"""
    version_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()
    
    class Meta:
        model = Standard
        fields = [
            'id', 'scope', 'tenant', 'code', 'name', 'owner',
            'description', 'version_count', 'latest_version'
        ]
        read_only_fields = ['id']
    
    def get_version_count(self, obj):
        return obj.versions.count()
    
    def get_latest_version(self, obj):
        latest = obj.get_latest_version()
        if latest:
            return {
                'id': str(latest.id),
                'version_label': latest.version_label,
                'released_on': latest.released_on
            }
        return None


class ControlNodeSerializer(serializers.ModelSerializer):
    """Serializer for ControlNode with hierarchy support"""
    hierarchy_path = serializers.CharField(source='get_hierarchy_path', read_only=True)
    children_count = serializers.SerializerMethodField()
    depth = serializers.IntegerField(source='get_depth', read_only=True)
    
    class Meta:
        model = ControlNode
        fields = [
            'id', 'standard_version', 'node_type', 'code', 'title',
            'description', 'parent', 'status', 'control_nature',
            'criticality_weight', 'metadata', 'hierarchy_path',
            'children_count', 'depth'
        ]
        read_only_fields = ['id']
    
    def get_children_count(self, obj):
        return obj.children.count()


class ControlNodeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing controls"""
    standard_code = serializers.CharField(source='standard_version.standard.code', read_only=True)
    parent_code = serializers.CharField(source='parent.code', read_only=True, allow_null=True)
    
    class Meta:
        model = ControlNode
        fields = [
            'id', 'code', 'title', 'node_type', 'status',
            'standard_code', 'parent_code', 'control_nature',
            'criticality_weight'
        ]
        read_only_fields = ['id']


class ControlNodeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single control view"""
    standard_code = serializers.CharField(source='standard_version.standard.code', read_only=True)
    standard_name = serializers.CharField(source='standard_version.standard.name', read_only=True)
    parent_code = serializers.CharField(source='parent.code', read_only=True, allow_null=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True, allow_null=True)
    children_count = serializers.SerializerMethodField()
    hierarchy_path = serializers.CharField(source='get_hierarchy_path', read_only=True)
    depth = serializers.IntegerField(source='get_depth', read_only=True)
    
    class Meta:
        model = ControlNode
        fields = [
            'id', 'standard_version', 'standard_code', 'standard_name',
            'node_type', 'code', 'title', 'description', 'parent',
            'parent_code', 'parent_title', 'status', 'control_nature',
            'criticality_weight', 'metadata', 'hierarchy_path',
            'children_count', 'depth'
        ]
        read_only_fields = ['id']
    
    def get_children_count(self, obj):
        return obj.children.count()


class ControlNodeTreeSerializer(serializers.ModelSerializer):
    """Serializer for hierarchical tree view"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlNode
        fields = [
            'id', 'code', 'title', 'node_type', 'status',
            'criticality_weight', 'children'
        ]
    
    def get_children(self, obj):
        children = obj.children.filter(status='active').order_by('code')
        return ControlNodeTreeSerializer(children, many=True).data


class ControlSearchSerializer(serializers.ModelSerializer):
    """Serializer for control search results"""
    standard_code = serializers.CharField(source='standard_version.standard.code', read_only=True)
    standard_name = serializers.CharField(source='standard_version.standard.name', read_only=True)
    version_label = serializers.CharField(source='standard_version.version_label', read_only=True)
    
    class Meta:
        model = ControlNode
        fields = [
            'id', 'code', 'title', 'description', 'node_type',
            'standard_code', 'standard_name', 'version_label',
            'control_nature', 'status'
        ]
        read_only_fields = ['id']


class StandardVersionSerializer(serializers.ModelSerializer):
    """Serializer for StandardVersion"""
    standard_code = serializers.CharField(source='standard.code', read_only=True)
    standard_name = serializers.CharField(source='standard.name', read_only=True)
    control_count = serializers.IntegerField(source='get_control_count', read_only=True)
    
    class Meta:
        model = StandardVersion
        fields = [
            'id', 'standard', 'standard_code', 'standard_name',
            'version_label', 'released_on', 'is_locked',
            'description', 'control_count'
        ]
        read_only_fields = ['id']


class ControlNodeTagSerializer(serializers.ModelSerializer):
    """Serializer for ControlNodeTag"""
    
    class Meta:
        model = ControlNodeTag
        fields = ['id', 'tenant', 'node', 'tag']
        read_only_fields = ['id']


class ControlMappingSerializer(serializers.ModelSerializer):
    """Serializer for ControlMapping"""
    source_code = serializers.CharField(source='source_node.code', read_only=True)
    target_code = serializers.CharField(source='target_node.code', read_only=True)
    
    class Meta:
        model = ControlMapping
        fields = [
            'id', 'tenant', 'source_node', 'source_code',
            'target_node', 'target_code', 'mapping_type',
            'confidence', 'notes'
        ]
        read_only_fields = ['id']


class TenantControlExtensionSerializer(serializers.ModelSerializer):
    """Serializer for TenantControlExtension"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = TenantControlExtension
        fields = [
            'id', 'tenant', 'base_node', 'custom_code', 'title',
            'description', 'status', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
