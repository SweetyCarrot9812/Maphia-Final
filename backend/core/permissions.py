# @SPEC:AUTH-001
# @TAG: @CODE:AUTH-005
"""
Custom permission classes for role-based access control (RBAC).
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that only allows Admin role users.

    Business Rules:
    - User must be authenticated
    - User role must be 'admin'
    """
    message = {
        "detail": "이 작업을 수행할 권한이 없습니다.",
        "required_role": "admin"
    }

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'admin'
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows Manager or Admin role users.

    Business Rules:
    - User must be authenticated
    - User role must be either 'admin' or 'manager'
    """
    message = {
        "detail": "이 작업을 수행할 권한이 없습니다.",
        "required_role": "manager"
    }

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role in ['admin', 'manager']
        )


class IsViewerOrAbove(permissions.BasePermission):
    """
    Permission class that allows all authenticated users (Viewer, Manager, Admin).

    Business Rules:
    - User must be authenticated
    - User role must be 'viewer', 'manager', or 'admin'
    """
    message = {
        "detail": "인증이 필요합니다.",
        "required_role": "viewer"
    }

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role in ['admin', 'manager', 'viewer']
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission that allows owners or admin users.

    Business Rules:
    - Admin users can access any object
    - Non-admin users can only access their own objects
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True

        # Check if object has uploaded_by or user field
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False
