"""
Authentication URL Configuration

@SPEC:AUTH-001
@CODE:AUTH-URLS
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.presentation.views import AuthViewSet, UserViewSet

# Create router
router = DefaultRouter()

# Register viewsets
# Note: We use basename for ViewSet (non-ModelViewSet)
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='users')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
