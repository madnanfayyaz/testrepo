"""
Assessment Models - Complete Advanced Version
Includes all models needed for full GRC assessment functionality
"""

from django.db import models
from django.utils import timezone
from standards.models import StandardVersion, ControlNode as Control
import uuid


class Assessment(models.Model):
    """
    Main assessment entity - represents a compliance assessment instance
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_PROGRESS', 'In Progress'),
        ('UNDER_REVIEW', 'Under Review'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='assessments')
    
    # Basic info
    code = models.CharField(max_length=50, unique=True, help_text="Unique assessment code")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    
    # Compliance standard
    standard_version = models.ForeignKey('standards.StandardVersion', on_delete=models.PROTECT)
    
    # Ownership
    owner_user = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_assessments')
    organization = models.ForeignKey('orgs.Organization', on_delete=models.CASCADE, null=True, blank=True)
    
    # Status and timeline
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assessments')
    
    class Meta:
        db_table = 'assessment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'code']),
        ]
    
    def __str__(self):
        return f"{self.code}: {self.name}"
    
    def get_progress_percentage(self):
        """Calculate assessment progress"""
        total = self.assessment_questions.count()
        if total == 0:
            return 0
        completed = self.assessment_questions.filter(
            response__status__in=['SUBMITTED', 'APPROVED']
        ).count()
        return round((completed / total) * 100, 2)
    
    @property
    def is_overdue(self):
        """Check if assessment is overdue"""
        if not self.due_date or self.status == 'COMPLETED':
            return False
        return timezone.now().date() > self.due_date


class AssessmentScope(models.Model):
    """
    Defines which controls are in scope for an assessment
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scopes')
    control_node = models.ForeignKey('standards.ControlNode', on_delete=models.CASCADE)
    include_children = models.BooleanField(default=True, help_text="Include child controls")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessment_scope'
        unique_together = [['assessment', 'control_node']]
        indexes = [
            models.Index(fields=['tenant', 'assessment']),
        ]


class AssessmentEntityScope(models.Model):
    """
    Maps assessments to specific entities (departments, systems, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='entity_scopes')
    
    # Entity can be department, system, region, etc.
    entity_type = models.CharField(max_length=50, help_text="department, system, region, etc.")
    entity_id = models.UUIDField(help_text="UUID of the entity")
    entity_name = models.CharField(max_length=255, help_text="Cached entity name")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessment_entity_scope'
        indexes = [
            models.Index(fields=['tenant', 'assessment']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]


class AssessmentQuestion(models.Model):
    """
    Materialized question instance for an assessment
    Snapshot of question at assessment creation time
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assessment_questions')
    
    # Link to source question (if from question bank)
    source_question = models.ForeignKey('question_bank.QuestionBank', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Control mapping
    control_node = models.ForeignKey('standards.ControlNode', on_delete=models.CASCADE)
    
    # Entity assignment (optional)
    department = models.ForeignKey('orgs.Department', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Question snapshot - captured at materialization time
    question_code = models.CharField(max_length=50)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, default='single_choice')
    scale_type = models.CharField(max_length=50, default='LIKERT_1_5')
    guidance = models.TextField(blank=True, default='')
    
    # Metadata
    pptdf_code = models.CharField(max_length=50, blank=True, default='')
    erl_refs = models.JSONField(default=list, blank=True)
    suggested_evidence_tags = models.JSONField(default=list, blank=True)
    
    # Display
    display_order = models.IntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessment_question'
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['tenant', 'assessment']),
            models.Index(fields=['control_node']),
        ]
    
    def __str__(self):
        return f"{self.question_code}: {self.question_text[:50]}"


class Assignment(models.Model):
    """
    Assigns assessment questions to specific users
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment_question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey('iam.AppUser', on_delete=models.CASCADE, related_name='question_assignments')
    assigned_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_questions')
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assignment'
        unique_together = [['assessment_question', 'assigned_to']]
        indexes = [
            models.Index(fields=['tenant', 'assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"Assignment: {self.assessment_question.question_code} → {self.assigned_to}"


class AssessmentProgress(models.Model):
    """
    Tracks overall assessment progress and metrics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='progress')
    
    total_questions = models.IntegerField(default=0)
    answered_questions = models.IntegerField(default=0)
    approved_questions = models.IntegerField(default=0)
    
    total_controls = models.IntegerField(default=0)
    assessed_controls = models.IntegerField(default=0)
    
    compliance_score = models.FloatField(default=0.0, help_text="Overall compliance score 0-100")
    maturity_score = models.FloatField(default=0.0, help_text="Average maturity score")
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessment_progress'


class AssessmentEvidence(models.Model):
    """
    Evidence attached at assessment level (not question-specific)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assessment_evidence')
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    file_path = models.CharField(max_length=500, blank=True, default='')
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True, default='')
    
    uploaded_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessment_evidence'
        ordering = ['-uploaded_at']


class AssessmentComment(models.Model):
    """
    Comments on assessment (not question-specific)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='assessment_comments')
    
    comment_text = models.TextField()
    author = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessment_comment'
        ordering = ['created_at']


class AssessmentSnapshot(models.Model):
    """
    Point-in-time snapshot of assessment state
    Used for audit trail and historical comparison
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='snapshots')
    
    snapshot_data = models.JSONField(help_text="Complete assessment state as JSON")
    snapshot_reason = models.CharField(max_length=255, help_text="Why snapshot was taken")
    
    created_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assessment_snapshot'
        ordering = ['-created_at']


# Keep backward compatibility with old Response models (from scaffold)
class Response(models.Model):
    """
    Response to an assessment question
    Note: Enhanced version is in responses app
    This is kept for backward compatibility
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment_question = models.OneToOneField(AssessmentQuestion, on_delete=models.CASCADE, related_name='response')
    selected_value = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, default='DRAFT')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'response'


class ResponseVersion(models.Model):
    """Response version history"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='versions')
    selected_value = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'response_version'


class QuestionComment(models.Model):
    """Comments on assessment questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    assessment_question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=255, blank=True, default='')
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_comment'
        ordering = ['created_at']
