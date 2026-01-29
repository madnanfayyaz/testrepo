"""
IAM URLs - API Routing for Authentication & User Management
With Optional JWT Support
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Try to import JWT views, but make optional
try:
    from rest_framework_simplejwt.views import TokenRefreshView
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    TokenRefreshView = None

from .views import (
    UserRegistrationView, UserLoginView, CustomTokenObtainPairView,
    UserProfileView, PasswordChangeView,
    AppUserViewSet, RoleViewSet, PermissionViewSet, UserRoleViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', AppUserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

# Base URL patterns (always available)
urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    
    # Include router URLs (users, roles, permissions, user-roles)
    path('', include(router.urls)),
]

# Add JWT routes only if JWT is available
if JWT_AVAILABLE and CustomTokenObtainPairView and TokenRefreshView:
    urlpatterns += [
        path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]

"""
API Endpoints Summary:

Authentication:
- POST   /api/iam/register/          Register new user
- POST   /api/iam/login/             Login with email + password
- POST   /api/iam/token/             Get JWT token (if JWT available)
- POST   /api/iam/token/refresh/     Refresh JWT token (if JWT available)

Profile:
- GET    /api/iam/profile/           Get own profile
- PATCH  /api/iam/profile/           Update own profile
- POST   /api/iam/change-password/   Change password

User Management:
- GET    /api/iam/users/                     List users
- POST   /api/iam/users/                     Create user
- GET    /api/iam/users/{id}/                Get user details
- PATCH  /api/iam/users/{id}/                Update user
- DELETE /api/iam/users/{id}/                Delete user
- POST   /api/iam/users/{id}/assign_role/    Assign role to user
- POST   /api/iam/users/{id}/remove_role/    Remove role from user
- POST   /api/iam/users/{id}/activate/       Activate user
- POST   /api/iam/users/{id}/deactivate/     Deactivate user

Role Management:
- GET    /api/iam/roles/                          List roles
- POST   /api/iam/roles/                          Create role
- GET    /api/iam/roles/{id}/                     Get role details
- PATCH  /api/iam/roles/{id}/                     Update role
- DELETE /api/iam/roles/{id}/                     Delete role
- POST   /api/iam/roles/{id}/assign_permission/   Assign permission
- POST   /api/iam/roles/{id}/remove_permission/   Remove permission

Permission Management:
- GET    /api/iam/permissions/        List all permissions
- GET    /api/iam/permissions/{id}/   Get permission details

User-Role Assignments:
- GET    /api/iam/user-roles/         List all user-role assignments
- POST   /api/iam/user-roles/         Create assignment
- DELETE /api/iam/user-roles/{id}/    Remove assignment
"""
