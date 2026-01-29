"""
Tenancy Models - Complete Implementation
Implements all tenant-related entities from ERD v3
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Tenant(models.Model):
    """
    Multi-tenant root entity. All other models reference this.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Tenant display name")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tenant-specific configuration (e.g., branding, features)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def is_active(self):
        return self.status == 'active'


class TenantRetentionPolicy(models.Model):
    """
    Data retention policies per tenant for compliance and storage management.
    """
    PURGE_MODE_CHOICES = [
        ('soft_delete', 'Soft Delete'),
        ('hard_delete', 'Hard Delete'),
        ('archive', 'Archive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='retention_policies'
    )
    object_type = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'assessment', 'response', 'evidence')"
    )
    retain_days = models.IntegerField(
        help_text="Number of days to retain data"
    )
    purge_mode = models.CharField(
        max_length=50,
        choices=PURGE_MODE_CHOICES,
        default='archive'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tenant_retention_policy'
        unique_together = [['tenant', 'object_type']]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.object_type} ({self.retain_days} days)"


class TenantFeatureFlag(models.Model):
    """
    Feature flags for enabling/disabling features per tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='feature_flags'
    )
    feature_code = models.CharField(
        max_length=100,
        help_text="Feature identifier (e.g., 'advanced_reporting', 'ai_suggestions')"
    )
    enabled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'tenant_feature_flag'
        unique_together = [['tenant', 'feature_code']]
        indexes = [
            models.Index(fields=['tenant', 'feature_code']),
        ]
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.tenant.name} - {self.feature_code} ({status})"


class Organization(models.Model):
    """
    Legal entity within a tenant. A tenant can have multiple organizations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='organizations'
    )
    legal_name = models.CharField(
        max_length=255,
        help_text="Official registered name"
    )
    sector = models.CharField(
        max_length=100,
        blank=True,
        help_text="Industry sector (e.g., 'Banking', 'Healthcare')"
    )
    regulator = models.CharField(
        max_length=100,
        blank=True,
        help_text="Primary regulatory body (e.g., 'SAMA', 'NCA')"
    )
    size_band = models.CharField(
        max_length=50,
        blank=True,
        help_text="Company size (e.g., 'SME', 'Enterprise', '100-500 employees')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization'
        unique_together = [['tenant', 'legal_name']]
        ordering = ['legal_name']
        indexes = [
            models.Index(fields=['tenant', 'sector']),
        ]
    
    def __str__(self):
        return f"{self.legal_name}"


class BusinessUnit(models.Model):
    """
    Hierarchical organizational structure (departments, teams, functions).
    Supports parent-child relationships for nested structures.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('merged', 'Merged'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='business_units'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='business_units',
        help_text="Optional: Link to parent organization"
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent business unit for hierarchical structure"
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'business_unit'
        unique_together = [['tenant', 'organization', 'name']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def clean(self):
        """Validate no circular parent references"""
        if self.parent:
            parent = self.parent
            visited = {self.id}
            while parent:
                if parent.id in visited:
                    raise ValidationError("Circular parent reference detected")
                visited.add(parent.id)
                parent = parent.parent
    
    def get_hierarchy_path(self):
        """Returns full path: Root > Parent > Child"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    def get_descendants(self):
        """Returns all child business units recursively"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Region(models.Model):
    """
    Geographic regions for compliance jurisdiction mapping.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='regions'
    )
    country = models.CharField(
        max_length=100,
        help_text="ISO country code or name (e.g., 'SA', 'AE')"
    )
    region = models.CharField(
        max_length=100,
        help_text="State/Province (e.g., 'Riyadh', 'Dubai')"
    )
    jurisdiction_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Legal jurisdiction code"
    )
    
    class Meta:
        db_table = 'region'
        unique_together = [['tenant', 'country', 'region', 'jurisdiction_code']]
        ordering = ['country', 'region']
    
    def __str__(self):
        return f"{self.region}, {self.country}"


class TechTag(models.Model):
    """
    Technology tags for categorizing systems and assets.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='tech_tags'
    )
    code = models.CharField(
        max_length=100,
        help_text="Tag code (e.g., 'AWS', 'AZURE', 'SAAS')"
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name"
    )
    
    class Meta:
        db_table = 'tech_tag'
        unique_together = [['tenant', 'code']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class SystemAsset(models.Model):
    """
    IT systems and assets to be tracked in compliance scope.
    """
    ASSET_TYPE_CHOICES = [
        ('application', 'Application'),
        ('database', 'Database'),
        ('infrastructure', 'Infrastructure'),
        ('network', 'Network'),
        ('endpoint', 'Endpoint'),
        ('cloud_service', 'Cloud Service'),
    ]
    
    CRITICALITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='system_assets'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='system_assets'
    )
    name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=100, choices=ASSET_TYPE_CHOICES)
    owner_bu = models.ForeignKey(
        BusinessUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_assets',
        help_text="Owning business unit"
    )
    criticality = models.CharField(
        max_length=50,
        choices=CRITICALITY_CHOICES,
        blank=True
    )
    tags = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (e.g., tech stack, compliance requirements)"
    )
    
    class Meta:
        db_table = 'system_asset'
        unique_together = [['tenant', 'organization', 'name']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'asset_type']),
            models.Index(fields=['criticality']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.asset_type})"
