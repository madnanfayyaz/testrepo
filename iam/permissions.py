"""
IAM Permissions - RBAC Permission System
Provides permission classes and decorators for access control
"""

from rest_framework import permissions
from functools import wraps
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from .models import Permission as PermissionModel


# ==========================================
# DRF Permission Classes
# ==========================================

class IsAuthenticated(permissions.BasePermission):
    """
    Allow access only to authenticated users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsTenantAdmin(permissions.BasePermission):
    """
    Allow access only to tenant administrators.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has 'Admin' role
        return request.user.user_roles.filter(role__name='Admin').exists()


class HasPermission(permissions.BasePermission):
    """
    Check if user has a specific permission.
    
    Usage:
        class MyView(APIView):
            permission_classes = [HasPermission]
            required_permission = 'assessment.create'
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required permission from view
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True  # No permission required
        
        return request.user.has_permission(required_permission)


class HasAnyPermission(permissions.BasePermission):
    """
    Check if user has any of the specified permissions.
    
    Usage:
        class MyView(APIView):
            permission_classes = [HasAnyPermission]
            required_permissions = ['assessment.view', 'assessment.create']
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get required permissions from view
        required_permissions = getattr(view, 'required_permissions', [])
        if not required_permissions:
            return True
        
        return request.user.has_any_permission(required_permissions)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission: allow owners and admins.
    Object must have 'owner_user_id' or 'created_by_id' field.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can access everything
        if request.user.user_roles.filter(role__name='Admin').exists():
            return True
        
        # Check ownership
        owner_id = getattr(obj, 'owner_user_id', None) or getattr(obj, 'created_by_id', None)
        return owner_id == request.user.id


class IsTenantMember(permissions.BasePermission):
    """
    Check if user belongs to the same tenant as the object.
    Object must have 'tenant' or 'tenant_id' field.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        obj_tenant_id = getattr(obj, 'tenant_id', None)
        if obj_tenant_id is None:
            obj_tenant = getattr(obj, 'tenant', None)
            obj_tenant_id = obj_tenant.id if obj_tenant else None
        
        return obj_tenant_id == request.user.tenant_id


# ==========================================
# Function Decorators
# ==========================================

def require_permission(permission_code):
    """
    Decorator to require a specific permission.
    
    Usage:
        @require_permission('assessment.create')
        def create_assessment(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise DjangoPermissionDenied("Authentication required")
            
            if not request.user.has_permission(permission_code):
                raise DjangoPermissionDenied(
                    f"Permission required: {permission_code}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_any_permission(*permission_codes):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission('assessment.view', 'assessment.edit')
        def view_assessment(request, assessment_id):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise DjangoPermissionDenied("Authentication required")
            
            if not request.user.has_any_permission(permission_codes):
                raise DjangoPermissionDenied(
                    f"One of these permissions required: {', '.join(permission_codes)}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_role(role_name):
    """
    Decorator to require a specific role.
    
    Usage:
        @require_role('Admin')
        def admin_only_view(request):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise DjangoPermissionDenied("Authentication required")
            
            has_role = request.user.user_roles.filter(role__name=role_name).exists()
            if not has_role:
                raise DjangoPermissionDenied(f"Role required: {role_name}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_tenant_admin(view_func):
    """
    Decorator to require tenant admin role.
    
    Usage:
        @require_tenant_admin
        def configure_tenant(request):
            # ...
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            raise DjangoPermissionDenied("Authentication required")
        
        is_admin = request.user.user_roles.filter(role__name='Admin').exists()
        if not is_admin:
            raise DjangoPermissionDenied("Tenant admin access required")
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


# ==========================================
# Helper Functions
# ==========================================

def check_permission(user, permission_code):
    """
    Check if user has a specific permission.
    
    Usage:
        if check_permission(request.user, 'assessment.create'):
            # Allow action
    """
    if not user or not user.is_authenticated:
        return False
    return user.has_permission(permission_code)


def get_user_permissions(user):
    """
    Get all permission codes for a user.
    
    Returns: List of permission codes (e.g., ['assessment.create', 'response.view'])
    """
    if not user or not user.is_authenticated:
        return []
    
    permissions = PermissionModel.objects.filter(
        rolepermission__role__userrole__user=user
    ).distinct().values_list('code', flat=True)
    
    return list(permissions)


def get_user_roles(user):
    """
    Get all role names for a user.
    
    Returns: List of role names (e.g., ['Admin', 'Compliance Officer'])
    """
    if not user or not user.is_authenticated:
        return []
    
    roles = user.get_roles().values_list('name', flat=True)
    return list(roles)


def has_scope_access(user, scope_type, scope_id):
    """
    Check if user has access to a specific scope (organization/business unit).
    
    Args:
        user: AppUser instance
        scope_type: 'organization' or 'business_unit'
        scope_id: UUID of the organization or business unit
    
    Returns: Boolean
    """
    if not user or not user.is_authenticated:
        return False
    
    # Global roles have access to everything
    if user.user_roles.filter(scope_type='global').exists():
        return True
    
    # Check specific scope
    return user.user_roles.filter(
        scope_type=scope_type,
        scope_id=scope_id
    ).exists()


def filter_by_user_scope(queryset, user, scope_field='organization_id'):
    """
    Filter queryset based on user's role scopes.
    
    Usage:
        assessments = Assessment.objects.all()
        assessments = filter_by_user_scope(assessments, request.user)
    
    Args:
        queryset: Django QuerySet
        user: AppUser instance
        scope_field: Field name for scope filtering (default: 'organization_id')
    
    Returns: Filtered QuerySet
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    # Admins and global roles see everything
    global_roles = user.user_roles.filter(scope_type='global')
    if global_roles.exists():
        return queryset
    
    # Filter by user's scopes
    user_scopes = user.user_roles.exclude(scope_type='global')
    
    # Get all scope IDs user has access to
    org_scopes = user_scopes.filter(scope_type='organization').values_list('scope_id', flat=True)
    bu_scopes = user_scopes.filter(scope_type='business_unit').values_list('scope_id', flat=True)
    
    # Build filter
    from django.db.models import Q
    scope_filter = Q()
    
    if org_scopes:
        scope_filter |= Q(**{f'{scope_field}__in': org_scopes})
    
    if bu_scopes and 'business_unit' in scope_field:
        scope_filter |= Q(**{f'{scope_field}__in': bu_scopes})
    
    return queryset.filter(scope_filter) if scope_filter else queryset.none()


# ==========================================
# Permission Checker Mixin
# ==========================================

class PermissionRequiredMixin:
    """
    Mixin for views that require specific permissions.
    
    Usage:
        class CreateAssessmentView(PermissionRequiredMixin, APIView):
            required_permission = 'assessment.create'
    """
    required_permission = None
    required_permissions = None  # For multiple permissions (any)
    
    def check_permissions(self, request):
        """Override to add permission check"""
        super().check_permissions(request)
        
        if not request.user or not request.user.is_authenticated:
            self.permission_denied(request, message="Authentication required")
        
        # Check single permission
        if self.required_permission:
            if not request.user.has_permission(self.required_permission):
                self.permission_denied(
                    request,
                    message=f"Permission required: {self.required_permission}"
                )
        
        # Check multiple permissions (any)
        if self.required_permissions:
            if not request.user.has_any_permission(self.required_permissions):
                self.permission_denied(
                    request,
                    message=f"One of these permissions required: {', '.join(self.required_permissions)}"
                )
