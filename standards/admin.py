"""
Standards Admin - Enhanced Admin Interface
Hierarchical control navigation and bulk import
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Standard, StandardVersion, ControlNode, ControlNodeTag,
    ControlMapping, TenantControlExtension
)


class StandardVersionInline(admin.TabularInline):
    model = StandardVersion
    extra = 0
    fields = ['version_label', 'released_on', 'is_locked']
    readonly_fields = ['released_on']


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'scope', 'tenant', 'owner', 'version_count']
    list_filter = ['scope', 'tenant', 'owner']
    search_fields = ['code', 'name', 'owner']
    readonly_fields = ['id']
    inlines = [StandardVersionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'scope', 'tenant', 'code', 'name', 'owner')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    
    def version_count(self, obj):
        count = obj.versions.count()
        if count > 0:
            url = reverse('admin:standards_standardversion_changelist') + f'?standard__id__exact={obj.id}'
            return format_html('<a href="{}">{} versions</a>', url, count)
        return '0 versions'
    version_count.short_description = 'Versions'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant').prefetch_related('versions')


class ControlNodeInline(admin.TabularInline):
    model = ControlNode
    extra = 0
    fields = ['code', 'title', 'node_type', 'status', 'display_order']
    readonly_fields = ['code', 'title', 'node_type']
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StandardVersion)
class StandardVersionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'standard_code', 'version_label', 'released_on', 'is_locked', 'control_count']
    list_filter = ['is_locked', 'standard__code', 'released_on']
    search_fields = ['version_label', 'standard__code', 'standard__name']
    readonly_fields = ['id']
    inlines = [ControlNodeInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'standard', 'version_label')
        }),
        ('Details', {
            'fields': ('released_on', 'is_locked', 'notes')
        }),
    )
    
    def standard_code(self, obj):
        return obj.standard.code
    standard_code.short_description = 'Standard'
    standard_code.admin_order_field = 'standard__code'
    
    def control_count(self, obj):
        count = obj.count_controls()
        if count > 0:
            url = reverse('admin:standards_controlnode_changelist') + f'?standard_version__id__exact={obj.id}'
            return format_html('<a href="{}">{} controls</a>', url, count)
        return '0 controls'
    control_count.short_description = 'Controls'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('standard')


class ControlNodeTagInline(admin.TabularInline):
    model = ControlNodeTag
    extra = 0
    fields = ['tag']


@admin.register(ControlNode)
class ControlNodeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'title_short', 'node_type', 'hierarchy_display',
        'status', 'criticality_weight', 'child_count'
    ]
    list_filter = [
        'node_type', 'status', 'control_nature',
        'standard_version__standard__code'
    ]
    search_fields = ['code', 'title', 'description']
    readonly_fields = ['id', 'hierarchy_display', 'level_display']
    inlines = [ControlNodeTagInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'standard_version', 'code', 'title')
        }),
        ('Hierarchy', {
            'fields': ('node_type', 'parent', 'hierarchy_display', 'level_display', 'display_order')
        }),
        ('Details', {
            'fields': ('description', 'status', 'control_nature', 'criticality_weight')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        """Truncate long titles"""
        if len(obj.title) > 60:
            return obj.title[:60] + '...'
        return obj.title
    title_short.short_description = 'Title'
    
    def hierarchy_display(self, obj):
        """Show full hierarchy path"""
        return obj.get_hierarchy_path()
    hierarchy_display.short_description = 'Hierarchy Path'
    
    def level_display(self, obj):
        """Show hierarchy level"""
        level = obj.get_level()
        indent = '→ ' * level
        return f"{indent}Level {level}"
    level_display.short_description = 'Level'
    
    def child_count(self, obj):
        count = obj.children.count()
        if count > 0:
            return format_html('<span style="color: blue;">{} children</span>', count)
        return format_html('<span style="color: gray;">Leaf node</span>')
    child_count.short_description = 'Children'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('standard_version__standard', 'parent').prefetch_related('children')


@admin.register(ControlNodeTag)
class ControlNodeTagAdmin(admin.ModelAdmin):
    list_display = ['node_code', 'tag', 'tenant']
    list_filter = ['tag', 'tenant']
    search_fields = ['tag', 'node__code', 'node__title']
    
    def node_code(self, obj):
        return f"{obj.node.code} - {obj.node.title[:40]}"
    node_code.short_description = 'Control'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('node', 'tenant')


@admin.register(ControlMapping)
class ControlMappingAdmin(admin.ModelAdmin):
    list_display = [
        'source_control_display', 'mapping_type', 'target_control_display',
        'confidence', 'tenant'
    ]
    list_filter = ['mapping_type', 'tenant']
    search_fields = [
        'source_node__code', 'source_node__title',
        'target_node__code', 'target_node__title'
    ]
    readonly_fields = ['id']
    
    fieldsets = (
        ('Mapping', {
            'fields': ('tenant', 'source_node', 'target_node', 'mapping_type')
        }),
        ('Details', {
            'fields': ('confidence', 'notes')
        }),
    )
    
    def source_control_display(self, obj):
        standard = obj.source_node.standard_version.standard.code
        return f"{standard}: {obj.source_node.code}"
    source_control_display.short_description = 'Source'
    
    def target_control_display(self, obj):
        standard = obj.target_node.standard_version.standard.code
        return f"{standard}: {obj.target_node.code}"
    target_control_display.short_description = 'Target'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'source_node__standard_version__standard',
            'target_node__standard_version__standard',
            'tenant'
        )


@admin.register(TenantControlExtension)
class TenantControlExtensionAdmin(admin.ModelAdmin):
    list_display = ['custom_code', 'title_short', 'base_control_display', 'status', 'tenant', 'owner_user']
    list_filter = ['status', 'tenant']
    search_fields = ['custom_code', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'custom_code', 'title')
        }),
        ('Details', {
            'fields': ('description', 'status', 'base_node')
        }),
        ('Ownership', {
            'fields': ('owner_user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_short.short_description = 'Title'
    
    def base_control_display(self, obj):
        if obj.base_node:
            return f"{obj.base_node.code} - {obj.base_node.title[:30]}"
        return format_html('<span style="color: gray;">No base control</span>')
    base_control_display.short_description = 'Extends'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('base_node', 'tenant', 'owner_user')
