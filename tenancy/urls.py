"""
Tenancy URLs - API Routing for Tenant Management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# TODO: Create ViewSets for tenancy models
# from .views import (
#     TenantViewSet, OrganizationViewSet, BusinessUnitViewSet
# )

# Create router
router = DefaultRouter()
# router.register(r'tenants', TenantViewSet, basename='tenant')
# router.register(r'organizations', OrganizationViewSet, basename='organization')
# router.register(r'business-units', BusinessUnitViewSet, basename='businessunit')

urlpatterns = [
    path('', include(router.urls)),
]

# Placeholder: We'll implement tenancy ViewSets in Phase 3
# For now, this file exists to prevent import errors
