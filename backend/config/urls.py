"""
URL configuration for University Data Visualization Dashboard.

Main URL patterns:
- /admin/ - Django admin interface
- /api/ - REST API endpoints (from dashboard app)
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Authentication API endpoints
    path('api/', include('users.urls')),

    # Dashboard API endpoints
    path('', include('dashboard.urls')),
]
