"""
Findings Models - Complete Advanced Version
Tracks compliance gaps, issues, and remediation efforts
"""

from django.db import models
from django.utils import timezone
import uuid


class Finding(models.Model):
    """
    Compliance gap or issue identified during assessment
    """
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
        ('INFORMATIONAL', 'Informational'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('RISK_ACCEPTED', 'Risk Accepted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='findings')
    
    # Links
    assessment = models.ForeignKey('assessments.Assessment', on_delete=models.CASCADE, related_name='findings', null=True, blank=True)
    response = models.ForeignKey('responses.Response', on_delete=models.SET_NULL, null=True, blank=True, related_name='findings')
    control_node = models.ForeignKey('standards.ControlNode', on_delete=models.PROTECT)
    
    # Finding details
    finding_number = models.CharField(max_length=50, unique=True, help_text="Auto-generated finding ID")
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OPEN')
    
    # Impact and recommendation
    impact = models.TextField(blank=True, default='', help_text="Business impact description")
    recommendation = models.TextField(blank=True, default='', help_text="Remediation recommendation")
    
    # Ownership
    identified_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='identified_findings')
    assigned_to = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_findings')
    
    # Timeline
    identified_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    closed_date = models.DateField(null=True, blank=True)
    
    # Metadata
    auto_generated = models.BooleanField(default=False, help_text="Auto-generated from low response scores")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finding'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'severity']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.finding_number}: {self.title}"
    
    @property
    def is_overdue(self):
        """Check if finding is overdue"""
        if not self.due_date or self.status in ['RESOLVED', 'CLOSED', 'RISK_ACCEPTED']:
            return False
        return timezone.now().date() > self.due_date
    
    def save(self, *args, **kwargs):
        # Auto-generate finding number if not set
        if not self.finding_number:
            # Get count of findings for this tenant
            count = Finding.objects.filter(tenant=self.tenant).count()
            self.finding_number = f"FND-{self.tenant.id.hex[:6].upper()}-{count + 1:04d}"
        super().save(*args, **kwargs)


class FindingSeverity(models.Model):
    """
    Custom severity levels per tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    risk_score = models.IntegerField(default=0, help_text="Numeric risk score 0-100")
    color_code = models.CharField(max_length=7, default='#808080', help_text="Hex color code")
    
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'finding_severity'
        verbose_name_plural = 'Finding severities'
        unique_together = [['tenant', 'name']]
        ordering = ['display_order', 'name']


class FindingStatus(models.Model):
    """
    Custom status values per tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    is_closed_status = models.BooleanField(default=False, help_text="Indicates finding is resolved")
    
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'finding_status'
        verbose_name_plural = 'Finding statuses'
        unique_together = [['tenant', 'name']]
        ordering = ['display_order', 'name']


class RemediationAction(models.Model):
    """
    Remediation plan for a finding
    """
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='remediation_actions')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    action_plan = models.TextField(help_text="Detailed action plan")
    
    owner = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_actions')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PLANNED')
    
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'remediation_action'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['finding', 'status']),
        ]


class RemediationTask(models.Model):
    """
    Individual tasks within a remediation action
    """
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    remediation_action = models.ForeignKey(RemediationAction, on_delete=models.CASCADE, related_name='tasks')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    assigned_to = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='TODO')
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'remediation_task'
        ordering = ['display_order', 'created_at']


class RiskAcceptance(models.Model):
    """
    Risk acceptance decision for a finding
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    finding = models.OneToOneField(Finding, on_delete=models.CASCADE, related_name='risk_acceptance')
    
    justification = models.TextField(help_text="Business justification for accepting risk")
    approved_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_risk_acceptances')
    approved_date = models.DateField()
    expiry_date = models.DateField(help_text="Date when acceptance expires and needs review")
    
    conditions = models.TextField(blank=True, default='', help_text="Conditions or limitations")
    compensating_controls = models.TextField(blank=True, default='', help_text="Alternative controls in place")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'risk_acceptance'
    
    @property
    def is_expired(self):
        """Check if risk acceptance has expired"""
        if not self.is_active:
            return True
        return timezone.now().date() > self.expiry_date


class FindingComment(models.Model):
    """
    Comments on findings for collaboration
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='comments')
    
    comment_text = models.TextField()
    author = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finding_comment'
        ordering = ['created_at']


class FindingHistory(models.Model):
    """
    Audit trail of changes to findings
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='history')
    
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    
    changed_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'finding_history'
        ordering = ['-changed_at']
        verbose_name_plural = 'Finding histories'
