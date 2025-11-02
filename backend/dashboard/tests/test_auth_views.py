"""
Tests for Authentication Views (ViewSets)

@SPEC:AUTH-001
@TEST:AUTH-VIEWS
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for DRF API client"""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Fixture for creating a test user"""
    return User.objects.create_user(
        username='testuser',
        password='TestPass123!',
        email='test@example.com',
        role='viewer'
    )


@pytest.fixture
def admin_user(db):
    """Fixture for creating an admin user"""
    return User.objects.create_user(
        username='adminuser',
        password='AdminPass123!',
        email='admin@example.com',
        role='admin'
    )


@pytest.mark.django_db
@pytest.mark.integration
class TestLoginView:
    """
    Tests for Login API endpoint.

    @TEST:AUTH-VIEW-001
    """

    def test_successful_login_returns_tokens(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-001
        Successful login should return access and refresh tokens
        """
        url = '/api/auth/login/'

        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'testuser'
        assert response.data['user']['role'] == 'viewer'

    def test_login_with_invalid_credentials(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-002
        Login with wrong password should return 401
        """
        url = '/api/auth/login/'

        data = {
            'username': 'testuser',
            'password': 'WrongPassword!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'error_code' in response.data

    def test_login_with_nonexistent_user(self, api_client):
        """
        @TEST:AUTH-VIEW-003
        Login with non-existent user should return 401
        """
        url = '/api/auth/login/'

        data = {
            'username': 'nonexistent',
            'password': 'TestPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

    def test_login_with_locked_account(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-004
        Login with locked account should return 403
        """
        # Lock account by 5 failed attempts
        from users.application.auth_service import LoginUseCase

        use_case = LoginUseCase()
        for _ in range(5):
            use_case.login('testuser', 'WrongPass!', '192.168.1.1', 'Test')

        url = '/api/auth/login/'
        data = {
            'username': 'testuser',
            'password': 'TestPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'locked' in response.data['message'].lower()

    def test_login_with_invalid_username_format(self, api_client):
        """
        @TEST:AUTH-VIEW-005
        Login with invalid username format should return 400
        """
        url = '/api/auth/login/'

        data = {
            'username': 'ab',  # Too short
            'password': 'TestPass123!',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_login_with_short_password(self, api_client):
        """
        @TEST:AUTH-VIEW-006
        Login with short password should return 400 (validation error)
        """
        url = '/api/auth/login/'

        data = {
            'username': 'testuser',
            'password': 'short',  # Too short
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0'
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data


@pytest.mark.django_db
@pytest.mark.integration
class TestLogoutView:
    """
    Tests for Logout API endpoint.

    @TEST:AUTH-VIEW-002
    """

    def test_successful_logout(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-007
        Successful logout should blacklist refresh token
        """
        # First login to get tokens
        refresh = RefreshToken.for_user(test_user)
        refresh_token = str(refresh)

        # Authenticate with access token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        url = '/api/auth/logout/'
        data = {'refresh_token': refresh_token}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'message' in response.data

        # Verify token is blacklisted
        from users.models import BlacklistedToken
        assert BlacklistedToken.is_blacklisted(refresh_token) is True

    def test_logout_without_authentication(self, api_client):
        """
        @TEST:AUTH-VIEW-008
        Logout without authentication should return 401
        """
        url = '/api/auth/logout/'
        data = {'refresh_token': 'fake.token.string'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_with_missing_refresh_token(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-009
        Logout without refresh_token should return 400
        """
        refresh = RefreshToken.for_user(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        url = '/api/auth/logout/'
        data = {}  # Missing refresh_token

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'refresh_token' in response.data


@pytest.mark.django_db
@pytest.mark.integration
class TestTokenRefreshView:
    """
    Tests for Token Refresh API endpoint.

    @TEST:AUTH-VIEW-003
    """

    def test_successful_token_refresh(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-010
        Valid refresh token should return new access token
        """
        refresh = RefreshToken.for_user(test_user)
        refresh_token = str(refresh)

        url = '/api/auth/refresh/'
        data = {'refresh_token': refresh_token}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert response.data['success'] is True

    def test_token_refresh_with_blacklisted_token(self, api_client, test_user):
        """
        @TEST:AUTH-VIEW-011
        Blacklisted refresh token should fail
        """
        from users.models import BlacklistedToken
        from django.utils import timezone
        from datetime import timedelta

        refresh = RefreshToken.for_user(test_user)
        refresh_token = str(refresh)

        # Blacklist the token
        expires_at = timezone.now() + timedelta(days=7)
        BlacklistedToken.objects.create(
            token=refresh_token,
            user=test_user,
            reason='logout',
            expires_at=expires_at
        )

        url = '/api/auth/refresh/'
        data = {'refresh_token': refresh_token}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

    def test_token_refresh_with_invalid_token(self, api_client):
        """
        @TEST:AUTH-VIEW-012
        Invalid refresh token should return 400
        """
        url = '/api/auth/refresh/'
        data = {'refresh_token': 'invalid.token.string'}

        response = api_client.post(url, data, format='json')

        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]
        assert response.data['success'] is False

    def test_token_refresh_with_missing_token(self, api_client):
        """
        @TEST:AUTH-VIEW-013
        Missing refresh_token should return 400
        """
        url = '/api/auth/refresh/'
        data = {}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'refresh_token' in response.data
