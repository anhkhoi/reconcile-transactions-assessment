"""Root URL configuration for the reconciliation service."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("reconciliation.urls")),
]
