"""
Standards URLs - API Routing for Standards & Controls
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StandardViewSet, StandardVersionViewSet, ControlNodeViewSet,
    ControlMappingViewSet, TenantControlExtensionViewSet
)

# Create router
router = DefaultRouter()
router.register(r'standards', StandardViewSet, basename='standard')
router.register(r'standard-versions', StandardVersionViewSet, basename='standardversion')
router.register(r'controls', ControlNodeViewSet, basename='controlnode')
router.register(r'control-mappings', ControlMappingViewSet, basename='controlmapping')
router.register(r'custom-controls', TenantControlExtensionViewSet, basename='customcontrol')

urlpatterns = [
    path('', include(router.urls)),
]

"""
API Endpoints Summary:

Standards:
- GET    /api/v1/standards/                      List all standards
- POST   /api/v1/standards/                      Create standard
- GET    /api/v1/standards/{id}/                 Get standard details
- PATCH  /api/v1/standards/{id}/                 Update standard
- DELETE /api/v1/standards/{id}/                 Delete standard
- GET    /api/v1/standards/{id}/versions/        Get all versions
- GET    /api/v1/standards/{id}/latest/          Get latest version

Standard Versions:
- GET    /api/v1/standard-versions/              List all versions
- POST   /api/v1/standard-versions/              Create version
- GET    /api/v1/standard-versions/{id}/         Get version details
- GET    /api/v1/standard-versions/{id}/tree/    Get control tree (hierarchical)
- GET    /api/v1/standard-versions/{id}/controls/ Get all controls (flat)
- GET    /api/v1/standard-versions/{id}/statistics/ Get statistics

Control Nodes:
- GET    /api/v1/controls/                       List controls
- GET    /api/v1/controls/{id}/                  Get control details
- GET    /api/v1/controls/{id}/children/         Get child controls
- GET    /api/v1/controls/{id}/ancestors/        Get parent hierarchy
- GET    /api/v1/controls/{id}/descendants/      Get all descendants
- POST   /api/v1/controls/{id}/add_tag/          Add tag to control
- POST   /api/v1/controls/{id}/remove_tag/       Remove tag
- GET    /api/v1/controls/search/?q=encryption   Search controls

Control Mappings:
- GET    /api/v1/control-mappings/               List mappings
- POST   /api/v1/control-mappings/               Create mapping
- GET    /api/v1/control-mappings/by_standard/?source=ISO_27001&target=NIST_CSF

Custom Controls:
- GET    /api/v1/custom-controls/                List tenant custom controls
- POST   /api/v1/custom-controls/                Create custom control
- GET    /api/v1/custom-controls/{id}/           Get custom control
- PATCH  /api/v1/custom-controls/{id}/           Update custom control
"""
