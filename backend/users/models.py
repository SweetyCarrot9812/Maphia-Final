"""
User authentication models for SPEC-AUTH-001.

@SPEC:AUTH-001
@CODE:AUTH-001

Models:
- User: Extended user model with role-based access control
- BlacklistedToken: Tracks revoked JWT refresh tokens
- AuthLog: Security audit log for authentication events
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.base_models import AbstractTimestampModel


class User(AbstractUser):
    """
    Custom User model extending AbstractUser with RBAC and security features.

    @CODE:AUTH-001

    Fields:
        role: User role for RBAC (admin/manager/viewer)
        full_name: User's full name
        department: Department affiliation
        phone: Contact phone number
        failed_login_attempts: Counter for brute force protection
        account_locked_until: Timestamp when account lockout expires
        last_login_ip: IP address of last successful login
        is_active: Account active status (default: True)

    Methods:
        is_admin(): Check if user has admin role
        is_manager_or_above(): Check if user has manager or admin role
        is_account_locked(): Check if account is currently locked
        reset_failed_attempts(): Reset failed login counter
        increment_failed_attempts(): Increment failed login counter and lock if needed
    """

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]

    # RBAC field
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        help_text="User role for role-based access control"
    )

    # Profile fields
    full_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="User's full name"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department affiliation"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )

    # Security fields for BR-009 (brute force protection)
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when account lockout expires (15 minutes after 5 failures)"
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of last successful login"
    )

    class Meta:
        db_table = 'users'
        ordering = ['username']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # @CODE:AUTH-001 - RBAC helper methods
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    def is_manager_or_above(self) -> bool:
        """Check if user has manager or admin role."""
        return self.role in ['admin', 'manager']

    # @CODE:AUTH-003 - Account lockout logic (BR-009)
    def is_account_locked(self) -> bool:
        """
        Check if account is currently locked due to failed login attempts.

        Returns:
            bool: True if account is locked and lockout period hasn't expired
        """
        if self.account_locked_until is None:
            return False

        # Check if lockout period has expired
        if timezone.now() >= self.account_locked_until:
            # Lockout expired, reset fields
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
            return False

        return True

    def reset_failed_attempts(self):
        """Reset failed login attempts counter (called on successful login)."""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])

    def increment_failed_attempts(self):
        """
        Increment failed login attempts and lock account if threshold reached.

        BR-009: Lock account for 15 minutes after 5 consecutive failures.
        """
        self.failed_login_attempts += 1

        # Lock account for 15 minutes after 5 failures
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=15)

        self.save(update_fields=['failed_login_attempts', 'account_locked_until'])


class BlacklistedToken(AbstractTimestampModel):
    """
    Tracks revoked JWT refresh tokens for logout functionality.

    @CODE:AUTH-006

    When a user logs out, their refresh token is added to this blacklist
    to prevent reuse even if the token hasn't expired yet.

    Fields:
        token: The JWT refresh token string (hashed)
        user: Reference to the user who owns this token
        reason: Reason for blacklisting (e.g., 'logout', 'password_change')
        expires_at: Token expiration timestamp
    """

    REASON_CHOICES = [
        ('logout', 'User Logout'),
        ('password_change', 'Password Changed'),
        ('security', 'Security Breach'),
        ('admin_revoke', 'Admin Revocation'),
    ]

    token = models.CharField(
        max_length=500,
        unique=True,
        help_text="JWT refresh token (hashed)"
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        help_text="User who owns this token"
    )
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='logout',
        help_text="Reason for blacklisting"
    )
    expires_at = models.DateTimeField(
        help_text="Token expiration timestamp"
    )

    class Meta:
        db_table = 'blacklisted_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Blacklisted token for {self.user.username} ({self.reason})"

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: JWT refresh token string

        Returns:
            bool: True if token is blacklisted and not expired
        """
        try:
            blacklisted = cls.objects.get(token=token)
            # Check if token blacklist entry is still valid
            if timezone.now() < blacklisted.expires_at:
                return True
            # Token expired, can be deleted
            blacklisted.delete()
            return False
        except cls.DoesNotExist:
            return False


class AuthLog(AbstractTimestampModel):
    """
    Security audit log for authentication events.

    @CODE:AUTH-LOG

    Tracks all authentication-related events for security monitoring
    and compliance purposes.

    Fields:
        user: Reference to the user (null for failed login attempts)
        username_attempted: Username used in login attempt
        event_type: Type of event (login_success, login_failed, etc.)
        ip_address: IP address of the request
        user_agent: Browser user agent string
        success: Whether the event was successful
        failure_reason: Reason for failure (if applicable)
    """

    EVENT_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('token_refresh', 'Token Refresh'),
        ('password_change', 'Password Change'),
        ('account_locked', 'Account Locked'),
    ]

    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auth_logs',
        help_text="User involved in the event (null for failed logins)"
    )
    username_attempted = models.CharField(
        max_length=150,
        help_text="Username used in the attempt"
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_CHOICES,
        help_text="Type of authentication event"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the request"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="Browser user agent string"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the event was successful"
    )
    failure_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Reason for failure (if applicable)"
    )
    details = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional details about the auth event (JSON)"
    )

    class Meta:
        db_table = 'auth_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_event_type_display()} - {self.username_attempted} from {self.ip_address}"
