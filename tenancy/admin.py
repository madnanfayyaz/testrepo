"""
Tenancy Admin - Enhanced Admin Interface
Provides intuitive management for all tenancy models
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Tenant, TenantRetentionPolicy, TenantFeatureFlag,
    Organization, BusinessUnit, Region, TechTag, SystemAsset
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at', 'feature_count', 'org_count']
    list_filter = ['status', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'status')
        }),
        ('Configuration', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def feature_count(self, obj):
        count = obj.feature_flags.filter(enabled=True).count()
        return format_html('<span style="color: green;">{} enabled</span>', count)
    feature_count.short_description = 'Features'
    
    def org_count(self, obj):
        return obj.organizations.count()
    org_count.short_description = 'Organizations'


class TenantRetentionPolicyInline(admin.TabularInline):
    model = TenantRetentionPolicy
    extra = 0
    fields = ['object_type', 'retain_days', 'purge_mode', 'is_active']


class TenantFeatureFlagInline(admin.TabularInline):
    model = TenantFeatureFlag
    extra = 0
    fields = ['feature_code', 'enabled']


@admin.register(TenantRetentionPolicy)
class TenantRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'object_type', 'retain_days', 'purge_mode', 'is_active']
    list_filter = ['purge_mode', 'is_active', 'tenant']
    search_fields = ['tenant__name', 'object_type']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'object_type')
        }),
        ('Retention Settings', {
            'fields': ('retain_days', 'purge_mode', 'is_active')
        }),
    )


@admin.register(TenantFeatureFlag)
class TenantFeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'feature_code', 'enabled_status']
    list_filter = ['enabled', 'tenant']
    search_fields = ['tenant__name', 'feature_code']
    
    def enabled_status(self, obj):
        if obj.enabled:
            return format_html('<span style="color: green;">✓ Enabled</span>')
        return format_html('<span style="color: red;">✗ Disabled</span>')
    enabled_status.short_description = 'Status'


class BusinessUnitInline(admin.TabularInline):
    model = BusinessUnit
    extra = 0
    fields = ['name', 'parent', 'status']
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['legal_name', 'tenant', 'sector', 'regulator', 'size_band', 'bu_count']
    list_filter = ['sector', 'regulator', 'tenant']
    search_fields = ['legal_name', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [BusinessUnitInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'legal_name')
        }),
        ('Details', {
            'fields': ('sector', 'regulator', 'size_band')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def bu_count(self, obj):
        return obj.business_units.count()
    bu_count.short_description = 'Business Units'


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'parent', 'hierarchy', 'status', 'child_count']
    list_filter = ['status', 'tenant', 'organization']
    search_fields = ['name', 'organization__legal_name']
    readonly_fields = ['id', 'hierarchy_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'organization', 'name')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'hierarchy_display', 'status')
        }),
    )
    
    def hierarchy(self, obj):
        return obj.get_hierarchy_path()
    hierarchy.short_description = 'Full Path'
    
    def hierarchy_display(self, obj):
        """Show full hierarchy in admin"""
        return obj.get_hierarchy_path()
    hierarchy_display.short_description = 'Hierarchy Path'
    
    def child_count(self, obj):
        count = obj.children.count()
        if count > 0:
            return format_html('<span style="color: blue;">{} children</span>', count)
        return '-'
    child_count.short_description = 'Children'


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['country', 'region', 'jurisdiction_code', 'tenant']
    list_filter = ['country', 'tenant']
    search_fields = ['country', 'region', 'jurisdiction_code']
    
    fieldsets = (
        (None, {
            'fields': ('tenant', 'country', 'region', 'jurisdiction_code')
        }),
    )


@admin.register(TechTag)
class TechTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'tenant', 'usage_count']
    list_filter = ['tenant']
    search_fields = ['name', 'code']
    
    def usage_count(self, obj):
        # This will work once SystemAsset has many-to-many with TechTag
        # For now, return placeholder
        return '-'
    usage_count.short_description = 'Used By Assets'


@admin.register(SystemAsset)
class SystemAssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_type', 'criticality', 'owner_bu', 'organization']
    list_filter = ['asset_type', 'criticality', 'tenant']
    search_fields = ['name', 'organization__legal_name', 'owner_bu__name']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'organization', 'name')
        }),
        ('Classification', {
            'fields': ('asset_type', 'criticality', 'owner_bu')
        }),
        ('Additional Metadata', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'organization', 'owner_bu')
