# @SPEC:AUTH-001
# @TAG: @TEST:AUTH-SERVICE
"""
TDD Tests for LoginUseCase service (Application Layer).

Tests the 9 business rules for authentication:
BR-001: Username format validation
BR-002: Password length validation
BR-003: User lookup by username
BR-004: Password hash verification
BR-005: JWT token generation
BR-007: Account lock check
BR-009: 5-failure account lock (15 min)
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestLoginUseCase:
    """Test LoginUseCase service class."""

    def test_successful_login_returns_tokens(self):
        """
        @TEST:AUTH-SERVICE-001 - Successful login returns access and refresh tokens
        BR-003, BR-004, BR-005: User lookup, password verification, token generation
        """
        from users.application.auth_service import LoginUseCase

        # Create test user
        user = User.objects.create_user(
            username='testuser',
            password='ValidPassword123!',
            role='manager'
        )

        # Execute login
        use_case = LoginUseCase()
        result = use_case.login(
            username='testuser',
            password='ValidPassword123!',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )

        # Assert success
        assert result['success'] is True
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['user']['id'] == user.id
        assert result['user']['username'] == 'testuser'
        assert result['user']['role'] == 'manager'

    def test_login_with_wrong_password_fails(self):
        """
        @TEST:AUTH-SERVICE-002 - Login with wrong password fails
        BR-004: Password verification fails
        BR-009: Failed attempts increment
        """
        from users.application.auth_service import LoginUseCase

        user = User.objects.create_user(
            username='testuser',
            password='CorrectPassword123!',
            role='viewer'
        )

        use_case = LoginUseCase()
        result = use_case.login(
            username='testuser',
            password='WrongPassword123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )

        # Assert failure
        assert result['success'] is False
        assert result['error_code'] == 'AUTH-001'
        assert 'Invalid credentials' in result['message']

        # Check failed attempts incremented
        user.refresh_from_db()
        assert user.failed_login_attempts == 1

    def test_login_with_nonexistent_user_fails(self):
        """
        @TEST:AUTH-SERVICE-003 - Login with non-existent username fails
        BR-003: User lookup fails
        """
        from users.application.auth_service import LoginUseCase

        use_case = LoginUseCase()
        result = use_case.login(
            username='nonexistent',
            password='Password123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )

        assert result['success'] is False
        assert result['error_code'] == 'AUTH-001'
        assert 'Invalid credentials' in result['message']

    def test_login_with_locked_account_fails(self):
        """
        @TEST:AUTH-SERVICE-004 - Login with locked account fails
        BR-007: Account lock check
        BR-009: Account locked after 5 failures
        """
        from users.application.auth_service import LoginUseCase

        # Create locked user
        user = User.objects.create_user(
            username='lockeduser',
            password='Password123!',
            role='viewer'
        )
        user.failed_login_attempts = 5
        user.account_locked_until = timezone.now() + timedelta(minutes=15)
        user.save()

        use_case = LoginUseCase()
        result = use_case.login(
            username='lockeduser',
            password='Password123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )

        assert result['success'] is False
        assert result['error_code'] == 'AUTH-003'
        assert 'Account is locked' in result['message']

    def test_successful_login_resets_failed_attempts(self):
        """
        @TEST:AUTH-SERVICE-005 - Successful login resets failed attempts counter
        BR-009: Reset failed attempts on success
        """
        from users.application.auth_service import LoginUseCase

        user = User.objects.create_user(
            username='testuser',
            password='Password123!',
            role='viewer'
        )
        user.failed_login_attempts = 3
        user.save()

        use_case = LoginUseCase()
        result = use_case.login(
            username='testuser',
            password='Password123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )

        assert result['success'] is True

        # Check failed attempts reset
        user.refresh_from_db()
        assert user.failed_login_attempts == 0

    def test_five_failed_logins_lock_account(self):
        """
        @TEST:AUTH-SERVICE-006 - 5 consecutive failed logins lock account
        BR-009: Account lockout after 5 failures
        """
        from users.application.auth_service import LoginUseCase

        user = User.objects.create_user(
            username='testuser',
            password='CorrectPassword123!',
            role='viewer'
        )

        use_case = LoginUseCase()

        # Fail 5 times
        for i in range(5):
            result = use_case.login(
                username='testuser',
                password='WrongPassword!',
                ip_address='192.168.1.1',
                user_agent='Test'
            )
            assert result['success'] is False

        # Check account is locked
        user.refresh_from_db()
        assert user.failed_login_attempts == 5
        assert user.account_locked_until is not None
        assert user.is_account_locked() is True

        # 6th attempt should return locked error
        result = use_case.login(
            username='testuser',
            password='CorrectPassword123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )
        assert result['success'] is False
        assert result['error_code'] == 'AUTH-003'

    def test_inactive_user_cannot_login(self):
        """
        @TEST:AUTH-SERVICE-007 - Inactive users cannot login
        """
        from users.application.auth_service import LoginUseCase

        user = User.objects.create_user(
            username='inactive',
            password='Password123!',
            role='viewer'
        )
        user.is_active = False
        user.save()

        use_case = LoginUseCase()
        result = use_case.login(
            username='inactive',
            password='Password123!',
            ip_address='192.168.1.1',
            user_agent='Test'
        )

        assert result['success'] is False
        assert 'inactive' in result['message'].lower()

    def test_login_creates_auth_log(self):
        """
        @TEST:AUTH-SERVICE-008 - Login creates AuthLog entry
        Security audit logging
        """
        from users.application.auth_service import LoginUseCase
        from users.models import AuthLog

        user = User.objects.create_user(
            username='testuser',
            password='Password123!',
            role='manager'
        )

        initial_log_count = AuthLog.objects.count()

        use_case = LoginUseCase()
        result = use_case.login(
            username='testuser',
            password='Password123!',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0'
        )

        assert result['success'] is True

        # Check AuthLog created
        assert AuthLog.objects.count() == initial_log_count + 1

        log = AuthLog.objects.latest('created_at')
        assert log.user == user
        assert log.event_type == 'login_success'
        assert log.ip_address == '192.168.1.100'
        assert log.success is True


@pytest.mark.django_db
@pytest.mark.unit
class TestLogoutUseCase:
    """Test logout functionality with token blacklisting."""

    def test_logout_blacklists_refresh_token(self):
        """
        @TEST:AUTH-SERVICE-009 - Logout adds refresh token to blacklist
        BR-006: Token blacklisting
        """
        from users.application.auth_service import LoginUseCase
        from users.models import BlacklistedToken
        from rest_framework_simplejwt.tokens import RefreshToken

        user = User.objects.create_user(
            username='testuser',
            password='Password123!',
            role='viewer'
        )

        # Generate token
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        use_case = LoginUseCase()
        result = use_case.logout(
            user=user,
            refresh_token=refresh_token
        )

        assert result['success'] is True

        # Check token is blacklisted
        assert BlacklistedToken.objects.filter(token=refresh_token).exists()

    def test_logout_creates_auth_log(self):
        """
        @TEST:AUTH-SERVICE-010 - Logout creates AuthLog entry
        """
        from users.application.auth_service import LoginUseCase
        from users.models import AuthLog
        from rest_framework_simplejwt.tokens import RefreshToken

        user = User.objects.create_user(
            username='testuser',
            password='Password123!',
            role='viewer'
        )

        refresh = RefreshToken.for_user(user)

        initial_log_count = AuthLog.objects.count()

        use_case = LoginUseCase()
        result = use_case.logout(
            user=user,
            refresh_token=str(refresh)
        )

        assert result['success'] is True
        assert AuthLog.objects.count() == initial_log_count + 1

        log = AuthLog.objects.latest('created_at')
        assert log.event_type == 'logout'
        assert log.user == user
