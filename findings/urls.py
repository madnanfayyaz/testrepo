"""Findings URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FindingViewSet, FindingSeverityViewSet,
    RemediationActionViewSet, RemediationTaskViewSet,
    RiskAcceptanceViewSet
)

router = DefaultRouter()
router.register(r'findings', FindingViewSet, basename='finding')
router.register(r'finding-severities', FindingSeverityViewSet, basename='severity')
router.register(r'remediation-actions', RemediationActionViewSet, basename='action')
router.register(r'remediation-tasks', RemediationTaskViewSet, basename='task')
router.register(r'risk-acceptances', RiskAcceptanceViewSet, basename='risk')

urlpatterns = [
    path('', include(router.urls)),
]