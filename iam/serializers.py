"""
IAM Serializers - Complete Version with Optional JWT
All serializers needed by views.py
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import AppUser, Role, Permission, RolePermission, UserRole
from tenancy.models import Tenant

# Try to import JWT, but make it optional
try:
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    TokenObtainPairSerializer = None


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'description', 'module']
        read_only_fields = ['id']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model with permissions"""
    permissions = PermissionSerializer(source='get_permissions', many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of permission codes to assign"
    )
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'is_system_role', 'description',
            'permissions', 'permission_codes'
        ]
        read_only_fields = ['id', 'is_system_role']
    
    def create(self, validated_data):
        permission_codes = validated_data.pop('permission_codes', [])
        tenant = self.context['request'].user.tenant
        
        role = Role.objects.create(tenant=tenant, **validated_data)
        
        # Assign permissions
        for code in permission_codes:
            try:
                permission = Permission.objects.get(code=code)
                RolePermission.objects.create(role=role, permission=permission)
            except Permission.DoesNotExist:
                pass
        
        return role


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole assignments"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_username', 'role', 'role_name', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']


class AppUserSerializer(serializers.ModelSerializer):
    """Serializer for AppUser model"""
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = AppUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'is_active', 'is_staff', 'tenant', 'roles', 'permissions',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'full_name']
    
    def get_roles(self, obj):
        return [ur.role.name for ur in obj.user_roles.select_related('role')]
    
    def get_permissions(self, obj):
        permissions = set()
        for ur in obj.user_roles.select_related('role').prefetch_related('role__role_permissions__permission'):
            for rp in ur.role.role_permissions.all():
                permissions.add(rp.permission.code)
        return list(permissions)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile view/edit"""
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = AppUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'roles', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'full_name']
    
    def get_roles(self, obj):
        return [ur.role.name for ur in obj.user_roles.select_related('role')]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    tenant_id = serializers.UUIDField(required=True)
    
    class Meta:
        model = AppUser
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'tenant_id']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check tenant exists
        try:
            tenant = Tenant.objects.get(id=attrs['tenant_id'])
            attrs['tenant'] = tenant
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({"tenant_id": "Invalid tenant ID."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        tenant = validated_data.pop('tenant')
        validated_data.pop('tenant_id')
        
        user = AppUser.objects.create_user(
            tenant=tenant,
            **validated_data
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        tenant_id = attrs.get('tenant_id')
        
        if username and password:
            # Try to find user
            try:
                if tenant_id:
                    user = AppUser.objects.get(username=username, tenant_id=tenant_id)
                else:
                    user = AppUser.objects.get(username=username)
            except AppUser.DoesNotExist:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
            except AppUser.MultipleObjectsReturned:
                raise serializers.ValidationError("Multiple users found. Please provide tenant_id.")
            
            # Check password
            if not user.check_password(password):
                raise serializers.ValidationError("Unable to log in with provided credentials.")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")
        
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True, required=True, label="Confirm New Password", style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# Only define JWT serializer if JWT is available
if JWT_AVAILABLE and TokenObtainPairSerializer:
    class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
        """Custom JWT token serializer with tenant info"""
        
        @classmethod
        def get_token(cls, user):
            token = super().get_token(user)
            
            # Add custom claims
            token['tenant_id'] = str(user.tenant_id)
            token['email'] = user.email
            token['full_name'] = user.full_name
            token['roles'] = [ur.role.name for ur in user.user_roles.select_related('role')]
            
            return token
else:
    # Dummy class if JWT not available
    class CustomTokenObtainPairSerializer:
        """Placeholder when JWT not available"""
        pass


# Alias for backward compatibility
LoginSerializer = UserLoginSerializer
