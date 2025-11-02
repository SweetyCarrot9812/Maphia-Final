"""
Authentication Serializers

@SPEC:AUTH-001
@CODE:AUTH-SERIALIZERS

Implements BR-001 and BR-002 validation rules.
"""

import re
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    @CODE:AUTH-SERIALIZER-001

    Business Rules:
    - BR-001: Username format validation (alphanumeric, 3-30 chars)
    - BR-002: Password length validation (8-128 chars)
    """

    username = serializers.CharField(
        min_length=3,
        max_length=30,
        required=True,
        help_text="Username (3-30 alphanumeric characters)"
    )

    password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Password (8-128 characters)"
    )

    ip_address = serializers.IPAddressField(
        required=False,
        default='0.0.0.0',
        help_text="Client IP address for audit logging"
    )

    user_agent = serializers.CharField(
        required=False,
        default='',
        allow_blank=True,
        max_length=500,
        help_text="Client user agent for audit logging"
    )

    def validate_username(self, value):
        """
        BR-001: Validate username format (alphanumeric only).

        Args:
            value: Username to validate

        Returns:
            Validated username

        Raises:
            ValidationError: If username contains invalid characters
        """
        # Allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username must contain only alphanumeric characters and underscores"
            )

        return value

    def validate_password(self, value):
        """
        BR-002: Validate password length.

        Args:
            value: Password to validate

        Returns:
            Validated password
        """
        # Length validation is handled by field definition (min_length, max_length)
        # Additional password complexity rules can be added here if needed
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.

    @CODE:AUTH-SERIALIZER-002

    Excludes sensitive fields like password hash.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'full_name',
            'department',
            'phone',
            'is_active',
            'last_login',
            'date_joined'
        ]
        read_only_fields = [
            'id',
            'username',
            'role',
            'is_active',
            'last_login',
            'date_joined'
        ]


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.

    @CODE:AUTH-SERIALIZER-003

    Requires refresh token for blacklisting.
    """

    refresh_token = serializers.CharField(
        required=True,
        help_text="JWT refresh token to blacklist"
    )


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh.

    @CODE:AUTH-SERIALIZER-004

    Requires refresh token to generate new access token.
    """

    refresh_token = serializers.CharField(
        required=True,
        help_text="JWT refresh token"
    )
