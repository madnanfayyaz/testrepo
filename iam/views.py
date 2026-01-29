"""
IAM Views - REST API Endpoints with Optional JWT
Provides: Registration, Login, User Management, Role Management
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

# Try to import JWT, but make it optional
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    from rest_framework_simplejwt.tokens import RefreshToken
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    TokenObtainPairView = None
    TokenRefreshView = None
    RefreshToken = None

from .models import AppUser, Role, Permission, UserRole
from .serializers import (
    AppUserSerializer, UserRegistrationSerializer, LoginSerializer,
    CustomTokenObtainPairSerializer, PasswordChangeSerializer,
    UserProfileSerializer, RoleSerializer, PermissionSerializer,
    UserRoleSerializer
)
from .permissions import IsAuthenticated, IsTenantAdmin


class UserRegistrationView(APIView):
    """
    API endpoint for user registration.
    POST /api/v1/auth/register/
    """
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            response_data = {
                'message': 'User registered successfully',
                'user': AppUserSerializer(user).data,
            }
            
            # Add JWT tokens if available
            if JWT_AVAILABLE and RefreshToken:
                refresh = RefreshToken.for_user(user)
                response_data['tokens'] = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API endpoint for user login with email + password.
    POST /api/v1/auth/login/
    """
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            response_data = {
                'message': 'Login successful',
                'user': AppUserSerializer(user).data,
            }
            
            # Add JWT tokens if available
            if JWT_AVAILABLE and RefreshToken:
                refresh = RefreshToken.for_user(user)
                response_data['tokens'] = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Only define JWT view if JWT is available
if JWT_AVAILABLE and TokenObtainPairView:
    class CustomTokenObtainPairView(TokenObtainPairView):
        """
        Custom JWT token endpoint with tenant info.
        POST /api/v1/auth/token/
        """
        serializer_class = CustomTokenObtainPairSerializer
else:
    # Placeholder if JWT not available
    CustomTokenObtainPairView = None


class UserProfileView(APIView):
    """
    API endpoint for viewing/updating own profile.
    GET/PATCH /api/v1/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    API endpoint for changing password.
    POST /api/v1/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    serializer_class = AppUserSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        # Filter by tenant
        return AppUser.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign a role to user"""
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id, tenant=request.user.tenant)
            UserRole.objects.get_or_create(user=user, role=role)
            return Response({'message': 'Role assigned successfully'})
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_role(self, request, pk=None):
        """Remove a role from user"""
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id, tenant=request.user.tenant)
            UserRole.objects.filter(user=user, role=role).delete()
            return Response({'message': 'Role removed successfully'})
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated successfully'})


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        return Role.objects.filter(tenant=self.request.user.tenant)
    
    @action(detail=True, methods=['post'])
    def assign_permission(self, request, pk=None):
        """Assign a permission to role"""
        role = self.get_object()
        permission_code = request.data.get('permission_code')
        
        try:
            permission = Permission.objects.get(code=permission_code)
            from .models import RolePermission
            RolePermission.objects.get_or_create(role=role, permission=permission)
            return Response({'message': 'Permission assigned successfully'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_permission(self, request, pk=None):
        """Remove a permission from role"""
        role = self.get_object()
        permission_code = request.data.get('permission_code')
        
        try:
            permission = Permission.objects.get(code=permission_code)
            from .models import RolePermission
            RolePermission.objects.filter(role=role, permission=permission).delete()
            return Response({'message': 'Permission removed successfully'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing permissions (read-only).
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Permission.objects.all()
    
    def get_queryset(self):
        queryset = Permission.objects.all()
        module = self.request.query_params.get('module', None)
        if module:
            queryset = queryset.filter(module=module)
        return queryset


class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user-role assignments.
    """
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        return UserRole.objects.filter(
            user__tenant=self.request.user.tenant
        ).select_related('user', 'role')
