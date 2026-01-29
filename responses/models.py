"""
Responses & Evidence Models
8 models: Response, ResponseVersion, ResponseReview, ResponseScoreRule,
          Evidence, EvidenceTag, EvidenceValidation, ResponseEvidence
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Response(models.Model):
    """Answer to an assessment question with maturity scoring"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='responses')
    assessment = models.ForeignKey('assessments.Assessment', on_delete=models.CASCADE, related_name='responses')
    assessment_question = models.ForeignKey('assessments.AssessmentQuestion', on_delete=models.CASCADE, related_name='responses')
    
    # Response data
    answer_payload = models.JSONField(help_text="Answer data (e.g., {'selected_option': 3})")
    maturity_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Ownership
    responder_user = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, related_name='responses_given')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='responses_approved')
    
    # Comments
    responder_comments = models.TextField(blank=True)
    reviewer_comments = models.TextField(blank=True)
    
    # Auto-population
    auto_populated = models.BooleanField(default=False)
    source_response_id = models.UUIDField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'response'
        unique_together = [['assessment', 'assessment_question']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'assessment']),
            models.Index(fields=['assessment_question']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.assessment.code} - {self.assessment_question.code}"
    
    def calculate_maturity_score(self):
        """Calculate maturity score based on answer"""
        if self.assessment_question.scale_type == 'LIKERT_1_5':
            selected = self.answer_payload.get('selected_option')
            if selected:
                self.maturity_score = float(selected)
        elif self.assessment_question.scale_type == 'YES_NO':
            selected = self.answer_payload.get('selected_option')
            self.maturity_score = 5.0 if selected == 1 else 1.0
        self.save()
        return self.maturity_score
    
    def submit(self):
        """Submit response for review"""
        if self.status != 'draft':
            raise ValidationError("Can only submit draft responses")
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
        self.calculate_maturity_score()
    
    def approve(self, approver_user):
        """Approve response"""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = approver_user
        self.save()
    
    def reject(self, reviewer_comments):
        """Reject response"""
        self.status = 'rejected'
        self.reviewer_comments = reviewer_comments
        self.save()


class ResponseVersion(models.Model):
    """Version history for responses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='response_versions')
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    answer_payload = models.JSONField()
    maturity_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    changed_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True)
    change_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'response_version'
        ordering = ['-version_number']
    
    def __str__(self):
        return f"{self.response} v{self.version_number}"


class ResponseReview(models.Model):
    """Review workflow for responses"""
    DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('clarification_needed', 'Clarification Needed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='response_reviews')
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='reviews')
    reviewer_user = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, related_name='reviews_conducted')
    decision = models.CharField(max_length=50, choices=DECISION_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'response_review'
        ordering = ['-reviewed_at']
    
    def __str__(self):
        return f"Review of {self.response}"


class ResponseScoreRule(models.Model):
    """Custom scoring rules"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='score_rules')
    control_node = models.ForeignKey('standards.ControlNode', on_delete=models.CASCADE, related_name='score_rules')
    weight_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'response_score_rule'
        unique_together = [['tenant', 'control_node']]
    
    def __str__(self):
        return f"Rule for {self.control_node.code}"


class Evidence(models.Model):
    """Evidence files supporting responses"""
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('spreadsheet', 'Spreadsheet'),
        ('video', 'Video'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='evidence')
    assessment = models.ForeignKey('assessments.Assessment', on_delete=models.CASCADE, related_name='evidence')
    
    # File info
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Metadata
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    
    # Ownership
    uploaded_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True, related_name='evidence_uploaded')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'evidence'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class EvidenceTag(models.Model):
    """Tags for evidence"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='evidence_tags')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='tags')
    tag = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'evidence_tag'
        unique_together = [['tenant', 'evidence', 'tag']]
    
    def __str__(self):
        return f"{self.evidence.title} - {self.tag}"


class EvidenceValidation(models.Model):
    """Validation history"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='evidence_validations')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='validations')
    validator_user = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True)
    is_valid = models.BooleanField()
    comments = models.TextField(blank=True)
    validated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evidence_validation'
        ordering = ['-validated_at']
    
    def __str__(self):
        return f"Validation of {self.evidence.title}"


class ResponseEvidence(models.Model):
    """Link responses to evidence"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='response_evidence_links')
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='evidence_links')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='response_links')
    linked_at = models.DateTimeField(auto_now_add=True)
    linked_by = models.ForeignKey('iam.AppUser', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'response_evidence'
        unique_together = [['response', 'evidence']]
    
    def __str__(self):
        return f"{self.response} ← {self.evidence.title}"