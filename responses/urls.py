"""Response URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResponseViewSet, ResponseReviewViewSet,
    EvidenceViewSet, ResponseEvidenceViewSet
)

router = DefaultRouter()
router.register(r'responses', ResponseViewSet, basename='response')
router.register(r'response-reviews', ResponseReviewViewSet, basename='review')
router.register(r'evidence', EvidenceViewSet, basename='evidence')
router.register(r'response-evidence', ResponseEvidenceViewSet, basename='link')

urlpatterns = [
    path('', include(router.urls)),
]