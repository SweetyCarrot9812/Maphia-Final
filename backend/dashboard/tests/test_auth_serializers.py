"""
Tests for Authentication Serializers

@SPEC:AUTH-001
@TEST:AUTH-SERIALIZERS
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestLoginSerializer:
    """
    Tests for LoginSerializer.

    Business Rules:
    - BR-001: Username format validation (alphanumeric, 3-30 chars)
    - BR-002: Password length validation (8-128 chars)
    """

    def test_valid_login_data(self):
        """
        @TEST:AUTH-SERIALIZER-001
        Valid username and password should pass validation
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'validuser123',
            'password': 'ValidPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is True
        assert serializer.validated_data['username'] == 'validuser123'

    def test_username_too_short(self):
        """
        @TEST:AUTH-SERIALIZER-002
        BR-001: Username less than 3 characters should fail
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'ab',
            'password': 'ValidPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'username' in serializer.errors

    def test_username_too_long(self):
        """
        @TEST:AUTH-SERIALIZER-003
        BR-001: Username longer than 30 characters should fail
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'a' * 31,
            'password': 'ValidPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'username' in serializer.errors

    def test_username_invalid_characters(self):
        """
        @TEST:AUTH-SERIALIZER-004
        BR-001: Username with special characters should fail
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'user@name!',
            'password': 'ValidPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'username' in serializer.errors

    def test_password_too_short(self):
        """
        @TEST:AUTH-SERIALIZER-005
        BR-002: Password less than 8 characters should fail
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'validuser',
            'password': 'Pass1!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_password_too_long(self):
        """
        @TEST:AUTH-SERIALIZER-006
        BR-002: Password longer than 128 characters should fail
        """
        from users.presentation.serializers import LoginSerializer

        data = {
            'username': 'validuser',
            'password': 'a' * 129,
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_missing_required_fields(self):
        """
        @TEST:AUTH-SERIALIZER-007
        Missing required fields should fail validation
        """
        from users.presentation.serializers import LoginSerializer

        data = {'username': 'validuser'}

        serializer = LoginSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password' in serializer.errors


@pytest.mark.django_db
@pytest.mark.unit
class TestUserSerializer:
    """Tests for UserSerializer"""

    def test_serialize_user_data(self):
        """
        @TEST:AUTH-SERIALIZER-008
        User data should be correctly serialized
        """
        from users.presentation.serializers import UserSerializer

        user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
            email='test@example.com',
            role='manager',
            full_name='Test User',
            department='Engineering'
        )

        serializer = UserSerializer(user)
        data = serializer.data

        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['role'] == 'manager'
        assert data['full_name'] == 'Test User'
        assert data['department'] == 'Engineering'
        assert 'password' not in data  # Password should not be exposed

    def test_user_serializer_read_only_fields(self):
        """
        @TEST:AUTH-SERIALIZER-009
        Sensitive fields should be read-only
        """
        from users.presentation.serializers import UserSerializer

        user = User.objects.create_user(username='testuser', password='test')

        # Try to update role via serializer (should be read-only)
        serializer = UserSerializer(user, data={'role': 'admin'}, partial=True)

        # Serializer should not allow role update through normal flow
        assert serializer.is_valid() is True
        # Role should remain unchanged after save
        serializer.save()
        user.refresh_from_db()
        assert user.role != 'admin'  # Should not change


@pytest.mark.django_db
@pytest.mark.unit
class TestLogoutSerializer:
    """Tests for LogoutSerializer"""

    def test_valid_refresh_token_field(self):
        """
        @TEST:AUTH-SERIALIZER-010
        Valid refresh token should pass validation
        """
        from users.presentation.serializers import LogoutSerializer

        data = {'refresh_token': 'valid.jwt.token.string'}

        serializer = LogoutSerializer(data=data)
        assert serializer.is_valid() is True

    def test_missing_refresh_token(self):
        """
        @TEST:AUTH-SERIALIZER-011
        Missing refresh_token should fail
        """
        from users.presentation.serializers import LogoutSerializer

        data = {}

        serializer = LogoutSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'refresh_token' in serializer.errors


@pytest.mark.django_db
@pytest.mark.unit
class TestTokenRefreshSerializer:
    """Tests for TokenRefreshSerializer"""

    def test_valid_token_refresh_data(self):
        """
        @TEST:AUTH-SERIALIZER-012
        Valid refresh token should pass validation
        """
        from users.presentation.serializers import TokenRefreshSerializer

        data = {'refresh_token': 'valid.jwt.token.string'}

        serializer = TokenRefreshSerializer(data=data)
        assert serializer.is_valid() is True

    def test_missing_refresh_token_in_refresh_serializer(self):
        """
        @TEST:AUTH-SERIALIZER-013
        Missing refresh_token should fail
        """
        from users.presentation.serializers import TokenRefreshSerializer

        data = {}

        serializer = TokenRefreshSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'refresh_token' in serializer.errors
