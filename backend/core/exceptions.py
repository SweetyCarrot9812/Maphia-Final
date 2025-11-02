# @SPEC:AUTH-001
# @TAG: @CODE:AUTH-002
"""
Custom exceptions for authentication and authorization.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class AccountLockedException(APIException):
    """
    Exception raised when user account is temporarily locked.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "계정이 잠겼습니다."
    default_code = 'ACCOUNT_LOCKED'


class InvalidCredentialsException(APIException):
    """
    Exception raised for invalid login credentials.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "아이디 또는 비밀번호가 올바르지 않습니다."
    default_code = 'INVALID_CREDENTIALS'


class TokenBlacklistedException(APIException):
    """
    Exception raised when using a blacklisted token.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "토큰이 무효화되었습니다."
    default_code = 'TOKEN_BLACKLISTED'


class InsufficientPermissionsException(APIException):
    """
    Exception raised when user lacks required permissions.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "이 작업을 수행할 권한이 없습니다."
    default_code = 'INSUFFICIENT_PERMISSIONS'
