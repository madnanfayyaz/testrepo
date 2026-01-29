"""
Standards Models - Compliance Framework Management
Implements: Standard, StandardVersion, ControlNode (hierarchical), ControlNodeTag, 
            ControlMapping, TenantControlExtension
"""

from django.db import models
from django.core.exceptions import ValidationError
import uuid


class Standard(models.Model):
    """
    Compliance standard/framework (e.g., ISO 27001, NCA ECC, NIST CSF).
    Can be global (shared across tenants) or tenant-specific.
    """
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('tenant', 'Tenant-Specific'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='global',
        help_text="Global standards are shared; tenant standards are private"
    )
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='standards',
        help_text="Required for tenant-specific standards"
    )
    code = models.CharField(
        max_length=100,
        help_text="Standard code (e.g., 'ISO27001', 'NCA_ECC', 'NIST_CSF')"
    )
    name = models.CharField(
        max_length=255,
        help_text="Full standard name"
    )
    owner = models.CharField(
        max_length=255,
        blank=True,
        help_text="Issuing organization (e.g., 'ISO', 'NCA', 'NIST')"
    )
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'standard'
        unique_together = [['scope', 'tenant', 'code']]
        ordering = ['code']
        indexes = [
            models.Index(fields=['scope', 'tenant']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_latest_version(self):
        """Get the most recent version of this standard"""
        return self.versions.filter(is_locked=False).order_by('-released_on').first()
    
    def get_all_versions(self):
        """Get all versions of this standard"""
        return self.versions.order_by('-released_on')


class StandardVersion(models.Model):
    """
    Versioned instance of a standard (e.g., ISO 27001:2022, ISO 27001:2013).
    Controls are associated with specific versions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_label = models.CharField(
        max_length=100,
        help_text="Version identifier (e.g., '2022', '2013', 'v1.0')"
    )
    released_on = models.DateField(
        null=True,
        blank=True,
        help_text="Official release date"
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Locked versions cannot be edited"
    )
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'standard_version'
        unique_together = [['standard', 'version_label']]
        ordering = ['-released_on']
        indexes = [
            models.Index(fields=['standard', 'is_locked']),
        ]
    
    def __str__(self):
        return f"{self.standard.code}:{self.version_label}"
    
    def get_control_count(self):
        """Count total controls in this version"""
        return self.control_nodes.filter(node_type='control').count()
    
    def get_hierarchy_root(self):
        """Get root-level nodes (domains)"""
        return self.control_nodes.filter(parent__isnull=True).order_by('code')


class ControlNode(models.Model):
    """
    Hierarchical control structure.
    Supports: Domain → Sub-domain → Control → Sub-control
    Each node can have a parent, creating a tree structure.
    """
    NODE_TYPE_CHOICES = [
        ('domain', 'Domain'),
        ('sub_domain', 'Sub-domain'),
        ('control', 'Control'),
        ('sub_control', 'Sub-control'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('draft', 'Draft'),
    ]
    
    CONTROL_NATURE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
        ('directive', 'Directive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_version = models.ForeignKey(
        StandardVersion,
        on_delete=models.CASCADE,
        related_name='control_nodes'
    )
    node_type = models.CharField(
        max_length=50,
        choices=NODE_TYPE_CHOICES,
        help_text="Type of node in the hierarchy"
    )
    code = models.CharField(
        max_length=100,
        help_text="Control code (e.g., 'A.5.1', 'A.5.1.1')"
    )
    title = models.TextField(
        help_text="Control title/name"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed control description"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent node for hierarchical structure"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active'
    )
    control_nature = models.CharField(
        max_length=100,
        choices=CONTROL_NATURE_CHOICES,
        blank=True,
        help_text="Nature of the control (for actual controls, not domains)"
    )
    criticality_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Weight for scoring calculations (0.0-5.0)"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata (implementation guidance, etc.)"
    )
    
    class Meta:
        db_table = 'control_node'
        unique_together = [['standard_version', 'node_type', 'code']]
        ordering = ['code']
        indexes = [
            models.Index(fields=['standard_version', 'node_type']),
            models.Index(fields=['parent']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title[:50]}"
    
    def clean(self):
        """Validate hierarchical consistency"""
        # Prevent circular references
        if self.parent:
            parent = self.parent
            visited = {self.id}
            while parent:
                if parent.id in visited:
                    raise ValidationError("Circular parent reference detected")
                visited.add(parent.id)
                parent = parent.parent
        
        # Validate node type hierarchy
        if self.parent:
            valid_hierarchies = {
                'sub_domain': ['domain'],
                'control': ['domain', 'sub_domain'],
                'sub_control': ['control'],
            }
            if self.node_type in valid_hierarchies:
                if self.parent.node_type not in valid_hierarchies[self.node_type]:
                    raise ValidationError(
                        f"{self.node_type} cannot have parent of type {self.parent.node_type}"
                    )
    
    def get_hierarchy_path(self):
        """Returns full path: Domain > Sub-domain > Control"""
        path = [self.code]
        parent = self.parent
        while parent:
            path.insert(0, parent.code)
            parent = parent.parent
        return ' > '.join(path)
    
    def get_full_path_title(self):
        """Returns full path with titles"""
        path = [f"{self.code} {self.title}"]
        parent = self.parent
        while parent:
            path.insert(0, f"{parent.code} {parent.title}")
            parent = parent.parent
        return ' > '.join(path)
    
    def get_descendants(self):
        """Returns all child nodes recursively"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_depth(self):
        """Calculate depth in hierarchy (0 = root)"""
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth
    
    def is_leaf(self):
        """Check if this is a leaf node (no children)"""
        return not self.children.exists()
    
    def get_sibling_count(self):
        """Count siblings at same level"""
        if self.parent:
            return self.parent.children.count()
        return self.standard_version.control_nodes.filter(parent__isnull=True).count()


class ControlNodeTag(models.Model):
    """
    Tags for categorizing controls (e.g., 'access_control', 'encryption', 'physical_security').
    Enables flexible filtering and grouping beyond the hierarchy.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='control_node_tags'
    )
    node = models.ForeignKey(
        ControlNode,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    tag = models.CharField(
        max_length=100,
        help_text="Tag value (e.g., 'access_control', 'encryption')"
    )
    
    class Meta:
        db_table = 'control_node_tag'
        unique_together = [['tenant', 'node', 'tag']]
        indexes = [
            models.Index(fields=['tenant', 'tag']),
            models.Index(fields=['node']),
        ]
    
    def __str__(self):
        return f"{self.node.code} - {self.tag}"


class ControlMapping(models.Model):
    """
    Maps controls across different standards (e.g., ISO 27001 A.5.1 → NCA ECC 1.1.1).
    Enables cross-standard assessments and gap analysis.
    """
    MAPPING_TYPE_CHOICES = [
        ('equivalent', 'Equivalent'),
        ('partial', 'Partial'),
        ('related', 'Related'),
        ('supersedes', 'Supersedes'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='control_mappings'
    )
    source_node = models.ForeignKey(
        ControlNode,
        on_delete=models.CASCADE,
        related_name='mappings_as_source'
    )
    target_node = models.ForeignKey(
        ControlNode,
        on_delete=models.CASCADE,
        related_name='mappings_as_target'
    )
    mapping_type = models.CharField(
        max_length=50,
        choices=MAPPING_TYPE_CHOICES,
        default='related'
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        help_text="Confidence level of mapping (0.0-1.0)"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'control_mapping'
        unique_together = [['tenant', 'source_node', 'target_node']]
        indexes = [
            models.Index(fields=['tenant', 'source_node']),
            models.Index(fields=['tenant', 'target_node']),
        ]
    
    def __str__(self):
        return f"{self.source_node.code} → {self.target_node.code} ({self.mapping_type})"


class TenantControlExtension(models.Model):
    """
    Tenant-specific custom controls that extend or supplement standard controls.
    Allows organizations to add their own controls beyond OOTB standards.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='custom_controls'
    )
    base_node = models.ForeignKey(
        ControlNode,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='extensions',
        help_text="Optional: Base control this extends"
    )
    custom_code = models.CharField(
        max_length=100,
        help_text="Custom control code"
    )
    title = models.TextField()
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_by = models.ForeignKey(
        'iam.AppUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_controls'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_control_extension'
        unique_together = [['tenant', 'custom_code']]
        ordering = ['custom_code']
        indexes = [
            models.Index(fields=['tenant', 'status']),
        ]
    
    def __str__(self):
        return f"{self.custom_code} - {self.title[:50]}"
