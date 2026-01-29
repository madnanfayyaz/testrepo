"""
Assessment Materialization - Creates assessment questions from question bank
"""

from django.db import transaction
from .models import Assessment, AssessmentQuestion
from question_bank.models import QuestionBank, ControlQuestionMap
from standards.models import ControlNode


def materialize_assessment_questions(assessment):
    """
    Materialize questions for an assessment based on its scope and standard version.
    
    Args:
        assessment: Assessment instance
    
    Returns:
        dict: Statistics about materialization
    """
    # Get all controls in scope for this assessment
    scoped_controls = get_scoped_controls(assessment)
    
    questions_created = 0
    controls_covered = 0
    
    with transaction.atomic():
        for control in scoped_controls:
            # Get questions mapped to this control
            question_maps = ControlQuestionMap.objects.filter(
                control_node=control,
                is_active=True
            ).select_related('question')
            
            if question_maps.exists():
                controls_covered += 1
            
            for qmap in question_maps:
                question = qmap.question
                
                # Create assessment question (snapshot)
                AssessmentQuestion.objects.create(
                    tenant=assessment.tenant,
                    assessment=assessment,
                    source_question=question,
                    control_node=control,
                    question_code=question.code,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    scale_type=question.scale_type,
                    guidance=question.guidance or '',
                    pptdf_code=question.pptdf_code or '',
                    erl_refs=question.erl_refs or [],
                    suggested_evidence_tags=question.suggested_evidence_tags or [],
                    display_order=qmap.display_order,
                    is_mandatory=qmap.is_mandatory
                )
                questions_created += 1
    
    return {
        'questions_created': questions_created,
        'controls_in_scope': scoped_controls.count(),
        'controls_with_questions': controls_covered,
        'status': 'success'
    }


def get_scoped_controls(assessment):
    """
    Get all controls in scope for an assessment.
    
    Args:
        assessment: Assessment instance
    
    Returns:
        QuerySet: ControlNode queryset
    """
    # If no explicit scopes defined, use all controls from the standard version
    if not assessment.scopes.exists():
        return ControlNode.objects.filter(
            standard_version=assessment.standard_version,
            status='active'
        )
    
    # Collect all controls from scopes
    control_ids = set()
    
    for scope in assessment.scopes.all():
        control_ids.add(scope.control_node.id)
        
        # If include_children, add all descendants
        if scope.include_children:
            descendants = scope.control_node.get_descendants()
            control_ids.update(descendants.values_list('id', flat=True))
    
    return ControlNode.objects.filter(
        id__in=control_ids,
        status='active'
    )


def rematerialize_assessment_questions(assessment):
    """
    Delete existing questions and re-materialize from current question bank.
    
    Warning: This will delete existing responses!
    
    Args:
        assessment: Assessment instance
    
    Returns:
        dict: Statistics about rematerialization
    """
    with transaction.atomic():
        # Delete existing questions (cascade will delete responses)
        deleted_count = assessment.assessment_questions.count()
        assessment.assessment_questions.all().delete()
        
        # Re-materialize
        result = materialize_assessment_questions(assessment)
        result['questions_deleted'] = deleted_count
        
    return result
