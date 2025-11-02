"""
Dashboard URL configuration for University Data Visualization Dashboard.

API Endpoints:
- /api/datasets/ - Dataset CRUD operations
- /api/records/ - DataRecord CRUD operations
- /api/statistics/ - Dashboard analytics
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatasetViewSet, DataRecordViewSet, StatisticsViewSet


# Create REST router
router = DefaultRouter()

# Register viewsets
router.register(r'datasets', DatasetViewSet, basename='dataset')
router.register(r'records', DataRecordViewSet, basename='datarecord')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

# URL patterns
urlpatterns = [
    path('api/', include(router.urls)),
]
