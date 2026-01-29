"""Helper functions for responses"""

from .models import Response


def get_suggested_response(tenant, question_bank_id):
    """
    Find previous approved response for auto-population.
    
    Returns:
        dict with suggested data, or None
    """
    previous = Response.objects.filter(
        tenant=tenant,
        assessment_question__question_bank_id=question_bank_id,
        status='approved'
    ).order_by('-approved_at').first()
    
    if previous:
        evidence_ids = list(previous.evidence_links.values_list('evidence_id', flat=True))
        return {
            'answer_payload': previous.answer_payload,
            'maturity_score': previous.maturity_score,
            'evidence_ids': evidence_ids,
            'responder_comments': previous.responder_comments,
            'source_assessment': previous.assessment.code,
            'source_date': previous.approved_at
        }
    return None


def calculate_control_maturity(control_node, assessment):
    """
    Calculate overall maturity for a control.
    
    Returns:
        float: Average maturity (0.0-5.0)
    """
    responses = Response.objects.filter(
        assessment=assessment,
        assessment_question__node_id=control_node.id,
        status='approved'
    )
    
    if not responses.exists():
        return None
    
    scores = [r.maturity_score for r in responses if r.maturity_score]
    return round(sum(scores) / len(scores), 2) if scores else 0.0