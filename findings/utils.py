"""Findings utility functions"""

from .models import Finding, auto_generate_finding


def generate_finding_for_response(response):
    """
    Check if response needs a finding and generate if needed.
    Called after response is submitted/approved.
    """
    return auto_generate_finding(response)


def get_findings_summary(tenant, assessment=None):
    """
    Get summary statistics for findings.
    
    Returns:
        dict with counts by severity and status
    """
    findings = Finding.objects.filter(tenant=tenant)
    if assessment:
        findings = findings.filter(assessment=assessment)
    
    by_severity = {}
    for severity, _ in Finding.SEVERITY_CHOICES:
        by_severity[severity] = findings.filter(severity=severity).count()
    
    by_status = {}
    for status, _ in Finding.STATUS_CHOICES:
        by_status[status] = findings.filter(status=status).count()
    
    return {
        'total': findings.count(),
        'by_severity': by_severity,
        'by_status': by_status,
        'overdue': len([f for f in findings if f.is_overdue()])
    }