"""
IAM Models - Identity & Access Management
Implements: AppUser, Role, Permission, RolePermission, UserRole
Supports: Multi-tenant RBAC with scope-based access
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class AppUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Multi-tenant aware with status tracking.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Activation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        help_text="Tenant this user belongs to"
    )
    # email inherited from AbstractUser, but we'll make it unique per tenant
    email = models.EmailField(
        'email address',
        help_text="Email must be unique within tenant"
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="User's full display name"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active'
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful login timestamp"
    )
    
    # Additional fields for security
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'app_user'
        unique_together = [['tenant', 'email']]
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['last_login_at']),
        ]
    
    def __str__(self):
        return f"{self.full_name or self.username} ({self.email})"
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def record_login(self):
        """Record successful login"""
        self.last_login_at = timezone.now()
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['last_login_at', 'failed_login_attempts', 'locked_until'])
    
    def record_failed_login(self, max_attempts=5, lockout_minutes=30):
        """Record failed login and lock account if threshold exceeded"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def get_roles(self):
        """Get all roles assigned to this user"""
        return Role.objects.filter(
            userrole__user=self
        ).distinct()
    
    def has_permission(self, permission_code):
        """Check if user has a specific permission"""
        return Permission.objects.filter(
            rolepermission__role__userrole__user=self,
            code=permission_code
        ).exists()
    
    def has_any_permission(self, permission_codes):
        """Check if user has any of the specified permissions"""
        return Permission.objects.filter(
            rolepermission__role__userrole__user=self,
            code__in=permission_codes
        ).exists()


class Role(models.Model):
    """
    Roles for RBAC (e.g., Admin, Compliance Officer, Responder).
    Can be system-defined or custom per tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='roles'
    )
    name = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Admin', 'Compliance Officer')"
    )
    is_system_role = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted or modified"
    )
    description = models.TextField(
        blank=True,
        help_text="Role description and responsibilities"
    )
    
    class Meta:
        db_table = 'role'
        unique_together = [['tenant', 'name']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_system_role']),
        ]
    
    def __str__(self):
        role_type = " (System)" if self.is_system_role else ""
        return f"{self.name}{role_type}"
    
    def get_permissions(self):
        """Get all permissions assigned to this role"""
        return Permission.objects.filter(
            rolepermission__role=self
        )
    
    def assign_permission(self, permission):
        """Assign a permission to this role"""
        RolePermission.objects.get_or_create(
            tenant=self.tenant,
            role=self,
            permission=permission
        )
    
    def remove_permission(self, permission):
        """Remove a permission from this role"""
        RolePermission.objects.filter(
            tenant=self.tenant,
            role=self,
            permission=permission
        ).delete()


class Permission(models.Model):
    """
    Granular permissions (e.g., 'assessment.create', 'response.approve').
    Global permissions shared across all tenants.
    """
    MODULE_CHOICES = [
        ('assessment', 'Assessment'),
        ('response', 'Response'),
        ('evidence', 'Evidence'),
        ('finding', 'Finding'),
        ('reporting', 'Reporting'),
        ('admin', 'Administration'),
        ('user', 'User Management'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Permission code (e.g., 'assessment.create', 'response.approve')"
    )
    description = models.TextField(
        blank=True,
        help_text="What this permission allows"
    )
    module = models.CharField(
        max_length=100,
        choices=MODULE_CHOICES,
        blank=True,
        help_text="Module this permission belongs to"
    )
    
    class Meta:
        db_table = 'permission'
        ordering = ['module', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.description[:50]}"


class RolePermission(models.Model):
    """
    Junction table: Assigns permissions to roles within a tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    
    class Meta:
        db_table = 'role_permission'
        unique_together = [['tenant', 'role', 'permission']]
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['role', 'permission']),
        ]
    
    def __str__(self):
        return f"{self.role.name} → {self.permission.code}"


class UserRole(models.Model):
    """
    Assigns roles to users with optional scope.
    Scope allows role to be limited to specific organization/business unit.
    
    Examples:
    - User X is 'Admin' globally (no scope)
    - User Y is 'Compliance Officer' for Organization A (scope_type='organization', scope_id=A.id)
    - User Z is 'Responder' for IT Department (scope_type='business_unit', scope_id=IT.id)
    """
    SCOPE_TYPE_CHOICES = [
        ('global', 'Global'),
        ('organization', 'Organization'),
        ('business_unit', 'Business Unit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    scope_type = models.CharField(
        max_length=50,
        choices=SCOPE_TYPE_CHOICES,
        default='global',
        help_text="Scope of this role assignment"
    )
    scope_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of organization or business unit (if scoped)"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made'
    )
    
    class Meta:
        db_table = 'user_role'
        unique_together = [['user', 'role', 'scope_type', 'scope_id']]
        indexes = [
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['user', 'role']),
            models.Index(fields=['scope_type', 'scope_id']),
        ]
    
    def __str__(self):
        scope_str = f" ({self.scope_type})" if self.scope_type != 'global' else ""
        return f"{self.user.username} → {self.role.name}{scope_str}"
    
    def clean(self):
        """Validate that scope_id is provided when scope_type is not global"""
        if self.scope_type != 'global' and not self.scope_id:
            raise ValidationError(
                f"scope_id is required when scope_type is '{self.scope_type}'"
            )
        if self.scope_type == 'global' and self.scope_id:
            raise ValidationError(
                "scope_id must be null when scope_type is 'global'"
            )
    
    def get_scope_object(self):
        """Get the actual organization or business unit object"""
        if self.scope_type == 'organization':
            from tenancy.models import Organization
            return Organization.objects.filter(id=self.scope_id).first()
        elif self.scope_type == 'business_unit':
            from tenancy.models import BusinessUnit
            return BusinessUnit.objects.filter(id=self.scope_id).first()
        return None


# Helper function to seed default permissions
def seed_default_permissions():
    """
    Create default permissions for the system.
    Should be called during initial setup.
    """
    permissions = [
        # Assessment permissions
        ('assessment.create', 'Create new assessments', 'assessment'),
        ('assessment.view', 'View assessments', 'assessment'),
        ('assessment.edit', 'Edit assessments', 'assessment'),
        ('assessment.delete', 'Delete assessments', 'assessment'),
        ('assessment.lock', 'Lock/unlock assessments', 'assessment'),
        
        # Response permissions
        ('response.submit', 'Submit responses', 'response'),
        ('response.view', 'View responses', 'response'),
        ('response.edit', 'Edit responses', 'response'),
        ('response.review', 'Review responses', 'response'),
        ('response.approve', 'Approve responses', 'response'),
        
        # Evidence permissions
        ('evidence.upload', 'Upload evidence', 'evidence'),
        ('evidence.view', 'View evidence', 'evidence'),
        ('evidence.delete', 'Delete evidence', 'evidence'),
        ('evidence.validate', 'Validate evidence', 'evidence'),
        
        # Finding permissions
        ('finding.create', 'Create findings', 'finding'),
        ('finding.view', 'View findings', 'finding'),
        ('finding.edit', 'Edit findings', 'finding'),
        ('finding.close', 'Close findings', 'finding'),
        
        # Remediation permissions
        ('remediation.create', 'Create remediation actions', 'finding'),
        ('remediation.assign', 'Assign remediation actions', 'finding'),
        ('remediation.update', 'Update remediation progress', 'finding'),
        
        # Reporting permissions
        ('report.generate', 'Generate reports', 'reporting'),
        ('report.export', 'Export reports', 'reporting'),
        ('dashboard.view', 'View dashboards', 'reporting'),
        
        # Admin permissions
        ('user.manage', 'Manage users', 'admin'),
        ('role.manage', 'Manage roles', 'admin'),
        ('tenant.configure', 'Configure tenant settings', 'admin'),
        ('standard.import', 'Import standards', 'admin'),
        
        # User permissions
        ('user.view_own', 'View own profile', 'user'),
        ('user.edit_own', 'Edit own profile', 'user'),
    ]
    
    created = []
    for code, description, module in permissions:
        perm, created_flag = Permission.objects.get_or_create(
            code=code,
            defaults={
                'description': description,
                'module': module
            }
        )
        if created_flag:
            created.append(perm)
    
    return created
