"""
Question Bank Models
Reusable question library with control mappings
"""

from django.db import models
import uuid


class QuestionBank(models.Model):
    """
    Reusable question library
    """
    QUESTION_TYPE_CHOICES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('text', 'Text'),
        ('file_upload', 'File Upload'),
    ]
    
    SCALE_TYPE_CHOICES = [
        ('LIKERT_1_5', 'Likert 1-5'),
        ('YES_NO', 'Yes/No'),
        ('TEXT', 'Text'),
        ('NUMERIC', 'Numeric'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE, related_name='question_bank')
    
    code = models.CharField(max_length=50, help_text="Unique question code (e.g., Q-POL-001)")
    question_text = models.TextField(help_text="The actual question")
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES, default='single_choice')
    guidance = models.TextField(blank=True, default='', help_text="Guidance for answering")
    scale_type = models.CharField(max_length=50, choices=SCALE_TYPE_CHOICES, default='LIKERT_1_5')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    pptdf_code = models.CharField(max_length=50, blank=True, default='', 
                                    help_text="People/Process/Technology/Data/Facility")
    erl_refs = models.JSONField(default=list, blank=True, help_text="External reference list")
    suggested_evidence_tags = models.JSONField(default=list, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'question_bank'
        unique_together = [['tenant', 'code']]
        ordering = ['code']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code}: {self.question_text[:50]}"
    
    def get_control_count(self):
        """Get number of mapped controls"""
        return self.control_mappings.count()
    
    def get_assessment_usage_count(self):
        """Get number of assessments using this question"""
        # This would need to link to assessment questions
        return 0


class QuestionBankOption(models.Model):
    """
    Answer options for question bank questions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='options')
    
    option_value = models.CharField(max_length=100, help_text="Internal value (e.g., '1', '2', 'yes', 'no')")
    option_text = models.CharField(max_length=255, help_text="Display text")
    score_weight = models.FloatField(default=0.0, help_text="Weight for scoring (e.g., 1.0, 2.0, 5.0)")
    description = models.TextField(blank=True, default='')
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_bank_option'
        ordering = ['display_order', 'option_value']
        indexes = [
            models.Index(fields=['question_bank', 'display_order']),
        ]
    
    def __str__(self):
        return f"{self.option_value}: {self.option_text}"


class ControlQuestionMap(models.Model):
    """
    Maps questions to compliance controls
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    control_node = models.ForeignKey('standards.ControlNode', on_delete=models.CASCADE, related_name='question_mappings')
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='control_mappings')
    
    rationale = models.TextField(blank=True, default='', help_text="Why this question maps to this control")
    criticality_override = models.FloatField(null=True, blank=True, help_text="Override control criticality for this mapping")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'control_question_map'
        unique_together = [['tenant', 'control_node', 'question_bank']]
        indexes = [
            models.Index(fields=['tenant', 'control_node']),
            models.Index(fields=['tenant', 'question_bank']),
        ]
    
    def __str__(self):
        return f"{self.control_node.code} → {self.question_bank.code}"


class QuestionApplicabilityRule(models.Model):
    """
    Rules for when questions apply
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='applicability_rules')
    
    rule_type = models.CharField(max_length=50, help_text="org_type, asset_type, etc.")
    rule_value = models.CharField(max_length=255)
    is_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_applicability_rule'
        indexes = [
            models.Index(fields=['tenant', 'question_bank']),
        ]


# Helper functions for creating default options
def create_default_likert_options(question_bank):
    """Create standard 1-5 Likert scale options"""
    options = [
        ('1', 'Not Implemented', 1.0, 'No implementation or evidence of this control'),
        ('2', 'Ad-Hoc', 2.0, 'Informal implementation without documentation'),
        ('3', 'Defined', 3.0, 'Documented and defined processes'),
        ('4', 'Managed', 4.0, 'Monitored and measured processes'),
        ('5', 'Optimized', 5.0, 'Continuously improving processes'),
    ]
    
    for idx, (value, text, score, desc) in enumerate(options):
        QuestionBankOption.objects.create(
            question_bank=question_bank,
            option_value=value,
            option_text=text,
            score_weight=score,
            description=desc,
            display_order=idx
        )


def create_yes_no_options(question_bank):
    """Create Yes/No options"""
    options = [
        ('yes', 'Yes', 5.0, 'Fully implemented'),
        ('no', 'No', 1.0, 'Not implemented'),
    ]
    
    for idx, (value, text, score, desc) in enumerate(options):
        QuestionBankOption.objects.create(
            question_bank=question_bank,
            option_value=value,
            option_text=text,
            score_weight=score,
            description=desc,
            display_order=idx
        )
