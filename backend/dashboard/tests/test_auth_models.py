# @SPEC:AUTH-001
# @TAG: @TEST:AUTH-001
"""
TDD Tests for authentication models (User, BlacklistedToken, AuthLog).

RED Phase: These tests will fail until we implement the models.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestUserModel:
    """
    Test suite for extended User model.
    Validates role field, security fields, and helper methods.
    """

    def test_user_creation_with_default_viewer_role(self):
        """
        @TEST:AUTH-001.1 - User role defaults to 'viewer'
        RED: Will fail until User model is extended with role field
        """
        user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!',
            email='test@example.com'
        )

        assert user.role == 'viewer'
        assert user.full_name == ''
        assert user.department == ''
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None

    def test_user_creation_with_admin_role(self):
        """
        @TEST:AUTH-001.2 - User can be created with admin role
        RED: Will fail until User model is extended
        """
        admin = User.objects.create_user(
            username='admin',
            password='AdminPassword123!',
            role='admin',
            full_name='김관리자',
            department='정보전산팀'
        )

        assert admin.role == 'admin'
        assert admin.full_name == '김관리자'
        assert admin.department == '정보전산팀'

    def test_is_admin_helper_method(self):
        """
        @TEST:AUTH-001.3 - is_admin() helper method
        RED: Will fail until helper method is implemented
        """
        admin = User.objects.create_user(username='admin', password='test', role='admin')
        manager = User.objects.create_user(username='manager', password='test', role='manager')
        viewer = User.objects.create_user(username='viewer', password='test', role='viewer')

        assert admin.is_admin() is True
        assert manager.is_admin() is False
        assert viewer.is_admin() is False

    def test_is_manager_or_above_helper_method(self):
        """
        @TEST:AUTH-001.4 - is_manager_or_above() helper method
        RED: Will fail until helper method is implemented
        """
        admin = User.objects.create_user(username='admin', password='test', role='admin')
        manager = User.objects.create_user(username='manager', password='test', role='manager')
        viewer = User.objects.create_user(username='viewer', password='test', role='viewer')

        assert admin.is_manager_or_above() is True
        assert manager.is_manager_or_above() is True
        assert viewer.is_manager_or_above() is False

    def test_failed_login_attempts_increment(self):
        """
        @TEST:AUTH-001.5 - Failed login attempts can be incremented
        RED: Will fail until security fields are added
        """
        user = User.objects.create_user(username='testuser', password='test')
        assert user.failed_login_attempts == 0

        user.failed_login_attempts += 1
        user.save()
        user.refresh_from_db()

        assert user.failed_login_attempts == 1

    def test_account_lockout_field(self):
        """
        @TEST:AUTH-001.6 - Account lockout timestamp can be set
        RED: Will fail until account_locked_until field is added
        """
        user = User.objects.create_user(username='testuser', password='test')
        lockout_time = timezone.now() + timedelta(minutes=15)

        user.account_locked_until = lockout_time
        user.save()
        user.refresh_from_db()

        assert user.account_locked_until == lockout_time


@pytest.mark.django_db
@pytest.mark.unit
class TestBlacklistedTokenModel:
    """
    Test suite for BlacklistedToken model.
    Validates token blacklisting for logout functionality.
    """

    def test_create_blacklisted_token(self):
        """
        @TEST:AUTH-002.1 - BlacklistedToken can be created
        RED: Will fail until BlacklistedToken model is implemented
        """
        from users.models import BlacklistedToken

        user = User.objects.create_user(username='testuser', password='test')
        refresh = RefreshToken.for_user(user)
        token_string = str(refresh)
        expires_at = timezone.now() + timedelta(days=7)

        blacklisted = BlacklistedToken.objects.create(
            token=token_string,
            user=user,
            reason='logout',
            expires_at=expires_at
        )

        assert blacklisted.token == token_string
        assert blacklisted.user == user
        assert blacklisted.reason == 'logout'
        assert blacklisted.created_at is not None  # AbstractTimestampModel provides created_at

    def test_blacklisted_token_uniqueness(self):
        """
        @TEST:AUTH-002.2 - Same token cannot be blacklisted twice
        RED: Will fail until unique constraint is added
        """
        from users.models import BlacklistedToken

        user = User.objects.create_user(username='testuser', password='test')
        refresh = RefreshToken.for_user(user)
        token_string = str(refresh)

        BlacklistedToken.objects.create(token=token_string, user=user, expires_at=timezone.now() + timedelta(days=7))

        # Attempting to create duplicate should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            BlacklistedToken.objects.create(token=token_string, user=user, expires_at=timezone.now() + timedelta(days=7))

    def test_blacklisted_token_query_by_token(self):
        """
        @TEST:AUTH-002.3 - Can query blacklisted tokens efficiently
        RED: Will fail until model is implemented with index
        """
        from users.models import BlacklistedToken

        user = User.objects.create_user(username='testuser', password='test')
        refresh = RefreshToken.for_user(user)
        token_string = str(refresh)

        BlacklistedToken.objects.create(token=token_string, user=user, expires_at=timezone.now() + timedelta(days=7))

        # Should be able to quickly check if token is blacklisted
        exists = BlacklistedToken.objects.filter(token=token_string).exists()
        assert exists is True


@pytest.mark.django_db
@pytest.mark.unit
class TestAuthLogModel:
    """
    Test suite for AuthLog model.
    Validates authentication event logging for security auditing.
    """

    def test_create_login_success_log(self):
        """
        @TEST:AUTH-003.1 - AuthLog can record login success
        RED: Will fail until AuthLog model is implemented
        """
        from users.models import AuthLog

        user = User.objects.create_user(username='testuser', password='test')

        log = AuthLog.objects.create(
            user=user,
            username_attempted=user.username,
            event_type='login_success',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        assert log.user == user
        assert log.event_type == 'login_success'
        assert log.ip_address == '192.168.1.1'
        assert log.success is True
        assert log.created_at is not None  # AbstractTimestampModel provides created_at

    def test_create_login_failure_log(self):
        """
        @TEST:AUTH-003.2 - AuthLog can record login failure
        RED: Will fail until AuthLog model is implemented
        """
        from users.models import AuthLog

        user = User.objects.create_user(username='testuser', password='test')

        log = AuthLog.objects.create(
            user=user,
            username_attempted=user.username,
            event_type='login_failure',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False
        )

        assert log.event_type == 'login_failure'
        assert log.success is False

    def test_auth_log_ordering(self):
        """
        @TEST:AUTH-003.3 - AuthLog orders by timestamp descending
        RED: Will fail until Meta.ordering is set
        """
        from users.models import AuthLog

        user = User.objects.create_user(username='testuser', password='test')

        log1 = AuthLog.objects.create(
            user=user,
            username_attempted=user.username,
            event_type='login_success',
            ip_address='192.168.1.1',
            user_agent='Test',
            success=True
        )

        # Add small delay to ensure different timestamps
        import time
        time.sleep(0.01)

        log2 = AuthLog.objects.create(
            user=user,
            username_attempted=user.username,
            event_type='logout',
            ip_address='192.168.1.1',
            user_agent='Test',
            success=True
        )

        logs = list(AuthLog.objects.all())
        assert logs[0] == log2  # Most recent first
        assert logs[1] == log1

    def test_auth_log_with_details_json(self):
        """
        @TEST:AUTH-003.4 - AuthLog can store additional details as JSON
        RED: Will fail until details JSONField is added
        """
        from users.models import AuthLog

        user = User.objects.create_user(username='testuser', password='test')

        log = AuthLog.objects.create(
            user=user,
            username_attempted=user.username,
            event_type='permission_denied',
            ip_address='192.168.1.1',
            user_agent='Test',
            success=False,
            details={'required_role': 'admin', 'current_role': 'viewer'}
        )

        assert log.details['required_role'] == 'admin'
        assert log.details['current_role'] == 'viewer'
