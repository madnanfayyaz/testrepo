"""Assessment URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssessmentViewSet, AssessmentScopeViewSet,
    AssessmentQuestionViewSet, AssignmentViewSet
)

router = DefaultRouter()
router.register(r'assessments', AssessmentViewSet, basename='assessment')
router.register(r'assessment-scopes', AssessmentScopeViewSet, basename='scope')
router.register(r'assessment-questions', AssessmentQuestionViewSet, basename='assessmentquestion')
router.register(r'assignments', AssignmentViewSet, basename='assignment')

urlpatterns = [
    path('', include(router.urls)),
]