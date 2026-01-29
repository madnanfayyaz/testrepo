"""
IAM Admin - Enhanced Admin Interface for User Management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AppUser, Role, Permission, RolePermission, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    fields = ['role', 'scope_type', 'scope_id', 'assigned_at']
    readonly_fields = ['assigned_at']


@admin.register(AppUser)
class AppUserAdmin(BaseUserAdmin):
    """Enhanced user admin with tenant and role management"""
    
    list_display = [
        'username', 'email', 'full_name', 'tenant', 'status',
        'roles_display', 'last_login_at', 'is_staff'
    ]
    list_filter = ['status', 'tenant', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'full_name']
    readonly_fields = ['id', 'last_login_at', 'date_joined', 'failed_login_attempts', 'locked_until']
    inlines = [UserRoleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'username', 'email', 'full_name')
        }),
        ('Tenant & Status', {
            'fields': ('tenant', 'status')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': (
                'password', 'must_change_password', 'password_changed_at',
                'failed_login_attempts', 'locked_until'
            ),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'last_login_at', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'tenant', 'password1', 'password2', 'status'),
        }),
    )
    
    def roles_display(self, obj):
        """Display roles as badges"""
        roles = obj.user_roles.select_related('role')[:3]
        if not roles:
            return format_html('<span style="color: gray;">No roles</span>')
        
        badges = []
        for ur in roles:
            color = 'green' if ur.scope_type == 'global' else 'blue'
            badges.append(
                f'<span style="background: {color}; color: white; padding: 2px 8px; '
                f'border-radius: 3px; margin-right: 4px;">{ur.role.name}</span>'
            )
        
        more = obj.user_roles.count() - len(roles)
        if more > 0:
            badges.append(f'<span style="color: gray;">+{more} more</span>')
        
        return format_html(''.join(badges))
    roles_display.short_description = 'Roles'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('tenant').prefetch_related('user_roles__role')


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    fields = ['permission', 'permission_description']
    readonly_fields = ['permission_description']
    
    def permission_description(self, obj):
        if obj.permission:
            return obj.permission.description
        return '-'
    permission_description.short_description = 'Description'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role management with permission assignment"""
    
    list_display = ['name', 'tenant', 'is_system_role', 'user_count', 'permission_count']
    list_filter = ['is_system_role', 'tenant']
    search_fields = ['name', 'description']
    readonly_fields = ['id']
    inlines = [RolePermissionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'name', 'is_system_role')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def user_count(self, obj):
        """Count users with this role"""
        count = obj.user_roles.count()
        if count > 0:
            url = reverse('admin:iam_appuser_changelist') + f'?user_roles__role__id__exact={obj.id}'
            return format_html('<a href="{}">{} users</a>', url, count)
        return '0 users'
    user_count.short_description = 'Users'
    
    def permission_count(self, obj):
        """Count permissions assigned to this role"""
        count = obj.role_permissions.count()
        return f'{count} permissions'
    permission_count.short_description = 'Permissions'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant').prefetch_related('role_permissions')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Permission management (read-only for most users)"""
    
    list_display = ['code', 'description_short', 'module', 'usage_count']
    list_filter = ['module']
    search_fields = ['code', 'description']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'code', 'module')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    def description_short(self, obj):
        """Truncate long descriptions"""
        if len(obj.description) > 60:
            return obj.description[:60] + '...'
        return obj.description
    description_short.short_description = 'Description'
    
    def usage_count(self, obj):
        """Count how many roles use this permission"""
        count = obj.role_permissions.count()
        return f'{count} roles'
    usage_count.short_description = 'Used By'
    
    def has_add_permission(self, request):
        """Only superusers can add permissions"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete permissions"""
        return request.user.is_superuser


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Junction table for role-permission assignments"""
    
    list_display = ['role', 'permission', 'tenant']
    list_filter = ['tenant', 'role']
    search_fields = ['role__name', 'permission__code']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant', 'role', 'permission')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """User-role assignments with scope"""
    
    list_display = [
        'user', 'role', 'scope_display', 'assigned_at', 'assigned_by'
    ]
    list_filter = ['scope_type', 'tenant', 'role']
    search_fields = ['user__username', 'user__email', 'role__name']
    readonly_fields = ['id', 'assigned_at']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('user', 'role', 'tenant')
        }),
        ('Scope', {
            'fields': ('scope_type', 'scope_id')
        }),
        ('Metadata', {
            'fields': ('assigned_at', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )
    
    def scope_display(self, obj):
        """Display scope with name"""
        if obj.scope_type == 'global':
            return format_html('<span style="color: green;">Global</span>')
        
        scope_obj = obj.get_scope_object()
        if scope_obj:
            return format_html(
                '<span style="color: blue;">{}: {}</span>',
                obj.scope_type.replace('_', ' ').title(),
                scope_obj
            )
        return f'{obj.scope_type}: {obj.scope_id}'
    scope_display.short_description = 'Scope'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'role', 'tenant', 'assigned_by')
