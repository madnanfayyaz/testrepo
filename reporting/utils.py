"""Reporting utility functions for metrics calculation"""

from assessments.models import Assessment
from findings.models import Finding
from responses.models import Response


def get_compliance_overview(tenant):
    """
    Get overall compliance overview with all metrics.
    
    Returns:
        dict with comprehensive metrics
    """
    return {
        'assessments': get_assessment_metrics(tenant),
        'findings': get_findings_metrics(tenant),
        'maturity': get_maturity_metrics(tenant),
        'remediation': get_remediation_metrics(tenant)
    }


def get_assessment_metrics(tenant, assessment_id=None):
    """
    Get assessment-related metrics.
    
    Returns:
        dict with assessment statistics
    """
    queryset = Assessment.objects.filter(tenant=tenant)
    if assessment_id:
        queryset = queryset.filter(id=assessment_id)
    
    total = queryset.count()
    
    # Count by status
    by_status = {}
    for status_code, status_label in Assessment.STATUS_CHOICES:
        by_status[status_code] = queryset.filter(status=status_code).count()
    
    # Calculate completion rate
    completed = by_status.get('completed', 0)
    completion_rate = round((completed / total * 100), 2) if total > 0 else 0
    
    # Count overdue
    overdue = len([a for a in queryset if a.is_overdue()])
    
    return {
        'total_assessments': total,
        'by_status': by_status,
        'completion_rate': completion_rate,
        'overdue': overdue
    }


def get_findings_metrics(tenant, assessment_id=None):
    """
    Get findings-related metrics.
    
    Returns:
        dict with findings statistics
    """
    queryset = Finding.objects.filter(tenant=tenant)
    if assessment_id:
        queryset = queryset.filter(assessment_id=assessment_id)
    
    total = queryset.count()
    
    # Count by severity
    by_severity = {}
    for severity_code, severity_label in Finding.SEVERITY_CHOICES:
        by_severity[severity_code] = queryset.filter(severity=severity_code).count()
    
    # Count by status
    by_status = {}
    for status_code, status_label in Finding.STATUS_CHOICES:
        by_status[status_code] = queryset.filter(status=status_code).count()
    
    # Count overdue
    overdue = len([f for f in queryset if f.is_overdue()])
    
    return {
        'total_findings': total,
        'by_severity': by_severity,
        'by_status': by_status,
        'overdue': overdue
    }


def get_maturity_metrics(tenant, assessment_id=None):
    """
    Get maturity score metrics.
    
    Returns:
        dict with maturity statistics
    """
    queryset = Response.objects.filter(
        tenant=tenant,
        status='approved'
    )
    if assessment_id:
        queryset = queryset.filter(assessment_id=assessment_id)
    
    scores = [r.maturity_score for r in queryset if r.maturity_score is not None]
    
    if not scores:
        return {
            'average_maturity': 0.0,
            'total_responses': 0,
            'score_distribution': {}
        }
    
    average = sum(scores) / len(scores)
    
    # Score distribution
    score_distribution = {
        '1.0-2.0': len([s for s in scores if 1.0 <= s < 2.0]),
        '2.0-3.0': len([s for s in scores if 2.0 <= s < 3.0]),
        '3.0-4.0': len([s for s in scores if 3.0 <= s < 4.0]),
        '4.0-5.0': len([s for s in scores if 4.0 <= s <= 5.0]),
    }
    
    return {
        'average_maturity': round(average, 2),
        'total_responses': len(scores),
        'score_distribution': score_distribution
    }


def get_remediation_metrics(tenant):
    """
    Get remediation progress metrics.
    
    Returns:
        dict with remediation statistics
    """
    from findings.models import RemediationAction
    
    queryset = RemediationAction.objects.filter(tenant=tenant)
    
    total = queryset.count()
    
    # Count by status
    by_status = {}
    for status_code, status_label in RemediationAction.STATUS_CHOICES:
        by_status[status_code] = queryset.filter(status=status_code).count()
    
    # Calculate average progress
    progress_values = [a.get_progress_percentage() for a in queryset]
    avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
    
    return {
        'total_actions': total,
        'by_status': by_status,
        'average_progress': round(avg_progress, 2)
    }


def get_metrics_data(tenant, data_source, config):
    """
    Get metrics data for a widget based on data_source.
    
    Args:
        tenant: Tenant instance
        data_source: Data source identifier
        config: Query configuration dict
    
    Returns:
        dict with metrics data
    """
    assessment_id = config.get('assessment_id')
    
    if data_source == 'assessments':
        return get_assessment_metrics(tenant, assessment_id)
    elif data_source == 'findings':
        return get_findings_metrics(tenant, assessment_id)
    elif data_source == 'responses':
        return get_maturity_metrics(tenant, assessment_id)
    elif data_source == 'remediation':
        return get_remediation_metrics(tenant)
    elif data_source == 'controls':
        # Could add control-specific metrics here
        return {'message': 'Controls metrics not yet implemented'}
    else:
        return {'error': 'Unknown data source'}