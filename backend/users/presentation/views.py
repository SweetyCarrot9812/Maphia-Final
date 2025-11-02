"""
Authentication ViewSets

@SPEC:AUTH-001
@CODE:AUTH-VIEWS
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

from users.presentation.serializers import (
    LoginSerializer,
    UserSerializer,
    LogoutSerializer,
    TokenRefreshSerializer
)
from users.application.auth_service import LoginUseCase

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication operations.

    @CODE:AUTH-VIEWSET-001

    Endpoints:
    - POST /api/auth/login/ - User login
    - POST /api/auth/logout/ - User logout
    - POST /api/auth/refresh/ - Refresh access token
    """

    def get_permissions(self):
        """
        Set permissions based on action.

        login, refresh: AllowAny (public endpoints)
        logout: IsAuthenticated (requires valid JWT)
        """
        if self.action in ['login', 'refresh']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_client_info(self, request):
        """
        Extract client IP and user agent from request.

        Args:
            request: HTTP request object

        Returns:
            tuple: (ip_address, user_agent)
        """
        # Get real IP from X-Forwarded-For if behind proxy
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')

        user_agent = request.META.get('HTTP_USER_AGENT', '')

        return ip_address, user_agent

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """
        User login endpoint.

        @CODE:AUTH-VIEWSET-LOGIN

        POST /api/auth/login/

        Request Body:
        {
            "username": "string",
            "password": "string",
            "ip_address": "string" (optional),
            "user_agent": "string" (optional)
        }

        Returns:
            200: Login successful with tokens
            400: Validation error
            401: Invalid credentials
            403: Account locked or inactive
        """
        # Get client info
        ip_address, user_agent = self.get_client_info(request)

        # Add client info to request data
        data = request.data.copy()
        if 'ip_address' not in data:
            data['ip_address'] = ip_address
        if 'user_agent' not in data:
            data['user_agent'] = user_agent

        # Validate request data
        serializer = LoginSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Execute login use case
        use_case = LoginUseCase()
        result = use_case.login(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            ip_address=serializer.validated_data['ip_address'],
            user_agent=serializer.validated_data['user_agent']
        )

        # Map error codes to HTTP status codes
        if not result['success']:
            error_code = result.get('error_code')

            if error_code in ['AUTH-001']:  # Invalid credentials
                return Response(result, status=status.HTTP_401_UNAUTHORIZED)
            elif error_code in ['AUTH-002']:  # Inactive account
                return Response(result, status=status.HTTP_403_FORBIDDEN)
            elif error_code in ['AUTH-003']:  # Account locked
                return Response(result, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Success response
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        User logout endpoint.

        @CODE:AUTH-VIEWSET-LOGOUT

        POST /api/auth/logout/

        Request Body:
        {
            "refresh_token": "string"
        }

        Returns:
            200: Logout successful
            400: Validation error
            401: Unauthorized (not authenticated)
        """
        # Get client info
        ip_address, user_agent = self.get_client_info(request)

        # Validate request data
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Execute logout use case
        use_case = LoginUseCase()
        result = use_case.logout(
            user=request.user,
            refresh_token=serializer.validated_data['refresh_token'],
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        """
        Refresh access token endpoint.

        @CODE:AUTH-VIEWSET-REFRESH

        POST /api/auth/refresh/

        Request Body:
        {
            "refresh_token": "string"
        }

        Returns:
            200: New access token generated
            400: Validation error
            401: Token revoked or invalid
        """
        # Validate request data
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Execute token refresh use case
        use_case = LoginUseCase()
        result = use_case.refresh_access_token(
            refresh_token=serializer.validated_data['refresh_token']
        )

        if not result['success']:
            error_code = result.get('error_code')

            if error_code in ['AUTH-005', 'AUTH-006']:  # Token revoked or invalid
                return Response(result, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user operations.

    @CODE:AUTH-VIEWSET-002

    Endpoints:
    - GET /api/users/ - List users (admin only)
    - GET /api/users/{id}/ - Retrieve user details
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter queryset based on user role.

        Admin: Can see all users
        Others: Can only see themselves
        """
        user = self.request.user

        if user.is_admin():
            return User.objects.all()

        # Non-admin users can only see themselves
        return User.objects.filter(id=user.id)
