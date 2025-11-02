# @SPEC:AUTH-001
# @TAG: @TEST:AUTH-001
"""
Pytest configuration for dashboard tests.
"""
import os
import django
import pytest


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


@pytest.fixture(scope='session', autouse=True)
def disable_throttling(django_db_setup, django_db_blocker):
    """
    Disable DRF throttling for tests.

    Rate limiting interferes with integration tests.
    """
    from django.conf import settings

    with django_db_blocker.unblock():
        # Store original settings
        original_throttle_classes = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_CLASSES', [])

        # Disable throttling
        settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

        yield

        # Restore original settings
        settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = original_throttle_classes
