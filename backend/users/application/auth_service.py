"""
LoginUseCase - Application Layer Service for Authentication

@SPEC:AUTH-001
@CODE:AUTH-SERVICE

Implements the 9 business rules for JWT authentication:
BR-001: Username format validation (handled by serializer)
BR-002: Password length validation (handled by serializer)
BR-003: User lookup by username
BR-004: Password hash verification
BR-005: JWT token generation
BR-006: Auth guard middleware (handled by DRF permissions)
BR-007: Account lock check
BR-008: 60-minute token lifetime (configured in settings)
BR-009: 5-failure account lock (15 minutes)
"""

from dataclasses import dataclass
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from typing import Dict, Any, Optional

from users.models import BlacklistedToken, AuthLog


User = get_user_model()


# Error code constants
class AuthErrorCodes:
    """Authentication error code constants."""
    INVALID_CREDENTIALS = 'AUTH-001'
    INACTIVE_ACCOUNT = 'AUTH-002'
    ACCOUNT_LOCKED = 'AUTH-003'
    LOGOUT_FAILED = 'AUTH-004'
    TOKEN_REVOKED = 'AUTH-005'
    TOKEN_REFRESH_FAILED = 'AUTH-006'


@dataclass
class AuthEventData:
    """Data structure for authentication event logging."""
    username: str
    event_type: str
    ip_address: str
    user_agent: str
    success: bool
    failure_reason: str = ''
    user: Optional[User] = None


class LoginUseCase:
    """
    Use case for handling user authentication (login/logout).

    @CODE:AUTH-SERVICE

    Responsibilities:
    - Validate credentials
    - Check account status (active, locked)
    - Generate JWT tokens
    - Track failed login attempts
    - Create security audit logs
    """

    def login(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """
        Authenticate user and return JWT tokens.

        @CODE:AUTH-SERVICE-001

        Business Rules Applied:
        - BR-003: User lookup by username
        - BR-004: Password hash verification
        - BR-005: JWT token generation
        - BR-007: Account lock check
        - BR-009: Failed login tracking and account lockout

        Args:
            username: Username to authenticate
            password: Plain text password
            ip_address: Client IP address for audit log
            user_agent: Client user agent for audit log

        Returns:
            Dict with success status, tokens (if success), or error details
            Success: {'success': True, 'access_token': str, 'refresh_token': str, 'user': dict}
            Failure: {'success': False, 'error_code': str, 'message': str}
        """
        # BR-003: User lookup by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Don't reveal whether username exists (security best practice)
            self._log_auth_event(AuthEventData(
                username=username,
                event_type='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='Invalid username'
            ))
            return self._error_response(
                AuthErrorCodes.INVALID_CREDENTIALS,
                'Invalid credentials'
            )

        # BR-007: Check if account is locked
        if user.is_account_locked():
            self._log_auth_event(AuthEventData(
                user=user,
                username=username,
                event_type='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='Account locked'
            ))
            return self._error_response(
                AuthErrorCodes.ACCOUNT_LOCKED,
                f'Account is locked. Try again after {user.account_locked_until.strftime("%H:%M")}'
            )

        # Check if account is active
        if not user.is_active:
            self._log_auth_event(AuthEventData(
                user=user,
                username=username,
                event_type='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='Account inactive'
            ))
            return self._error_response(
                AuthErrorCodes.INACTIVE_ACCOUNT,
                'Account is inactive. Please contact administrator.'
            )

        # BR-004: Password hash verification
        if not user.check_password(password):
            # BR-009: Increment failed login attempts
            user.increment_failed_attempts()

            self._log_auth_event(AuthEventData(
                user=user,
                username=username,
                event_type='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='Invalid password'
            ))

            # Check if account is now locked after this failure
            if user.is_account_locked():
                return self._error_response(
                    AuthErrorCodes.ACCOUNT_LOCKED,
                    'Too many failed attempts. Account locked for 15 minutes.'
                )

            return self._error_response(
                AuthErrorCodes.INVALID_CREDENTIALS,
                'Invalid credentials'
            )

        # Login successful!

        # BR-009: Reset failed login attempts on success
        user.reset_failed_attempts()

        # Update last login info
        user.last_login = timezone.now()
        user.last_login_ip = ip_address
        user.save(update_fields=['last_login', 'last_login_ip'])

        # BR-005: JWT token generation
        refresh = RefreshToken.for_user(user)

        # Add custom claims to token
        refresh['role'] = user.role
        refresh['username'] = user.username

        # Create success audit log
        self._log_auth_event(AuthEventData(
            user=user,
            username=username,
            event_type='login_success',
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        ))

        return self._success_response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': self._serialize_user(user)
        })

    def logout(
        self,
        user: User,
        refresh_token: str,
        ip_address: str = '0.0.0.0',
        user_agent: str = ''
    ) -> Dict[str, Any]:
        """
        Logout user by blacklisting refresh token.

        @CODE:AUTH-SERVICE-002

        Business Rules:
        - BR-006: Token blacklisting to prevent reuse

        Args:
            user: User object
            refresh_token: JWT refresh token to blacklist
            ip_address: Client IP for audit log
            user_agent: Client user agent for audit log

        Returns:
            Dict with success status
        """
        try:
            # Parse token to get expiration
            token_obj = RefreshToken(refresh_token)
            expires_at = timezone.datetime.fromtimestamp(
                token_obj['exp'],
                tz=timezone.get_current_timezone()
            )

            # Add to blacklist
            BlacklistedToken.objects.create(
                token=refresh_token,
                user=user,
                reason='logout',
                expires_at=expires_at
            )

            # Create logout audit log
            self._log_auth_event(AuthEventData(
                user=user,
                username=user.username,
                event_type='logout',
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            ))

            return self._success_response({'message': 'Logged out successfully'})

        except TokenError as e:
            return self._error_response(
                AuthErrorCodes.LOGOUT_FAILED,
                f'Invalid token: {str(e)}'
            )
        except Exception as e:
            return self._error_response(
                AuthErrorCodes.LOGOUT_FAILED,
                f'Logout failed: {str(e)}'
            )

    def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Generate new access token from refresh token.

        @CODE:AUTH-SERVICE-003

        Business Rules:
        - BR-006: Check if refresh token is blacklisted
        - BR-008: Generate new access token with 60-minute lifetime

        Args:
            refresh_token: JWT refresh token

        Returns:
            Dict with new access token or error
        """
        # Check if token is blacklisted
        if BlacklistedToken.is_blacklisted(refresh_token):
            return self._error_response(
                AuthErrorCodes.TOKEN_REVOKED,
                'Token has been revoked'
            )

        try:
            token_obj = RefreshToken(refresh_token)

            # Generate new access token
            new_access_token = str(token_obj.access_token)

            return self._success_response({'access_token': new_access_token})

        except TokenError as e:
            return self._error_response(
                AuthErrorCodes.TOKEN_REFRESH_FAILED,
                f'Invalid token: {str(e)}'
            )
        except Exception as e:
            return self._error_response(
                AuthErrorCodes.TOKEN_REFRESH_FAILED,
                f'Token refresh failed: {str(e)}'
            )

    # Helper methods

    def _log_auth_event(self, event_data: AuthEventData):
        """
        Create authentication audit log entry.

        Args:
            event_data: AuthEventData object with all required fields
        """
        AuthLog.objects.create(
            user=event_data.user,
            username_attempted=event_data.username,
            event_type=event_data.event_type,
            ip_address=event_data.ip_address,
            user_agent=event_data.user_agent,
            success=event_data.success,
            failure_reason=event_data.failure_reason
        )

    def _error_response(self, error_code: str, message: str) -> Dict[str, Any]:
        """
        Create standardized error response.

        Args:
            error_code: Error code constant
            message: Human-readable error message

        Returns:
            Dict with error details
        """
        return {
            'success': False,
            'error_code': error_code,
            'message': message
        }

    def _success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create standardized success response.

        Args:
            data: Success response data

        Returns:
            Dict with success status and data
        """
        return {
            'success': True,
            **data
        }

    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """
        Serialize user data for response.

        Args:
            user: User object

        Returns:
            Dict with user data
        """
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'full_name': user.full_name,
            'department': user.department
        }
