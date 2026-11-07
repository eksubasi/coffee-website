"""Root URL configuration for the Brewnook backend."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("catalog.urls")),
]
