# @SPEC:AUTH-001
# @TAG: @CODE:AUTH-001
"""
Base model classes for the application.
Provides common fields and functionality for all models.
"""
from django.db import models


class AbstractTimestampModel(models.Model):
    """
    Abstract base model that provides timestamp fields.

    Attributes:
        created_at: Timestamp when the object was created
        updated_at: Timestamp when the object was last updated
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시각")
    updated_at = models.DateTimeField(auto_now=True, help_text="마지막 수정 시각")

    class Meta:
        abstract = True
        ordering = ['-created_at']
