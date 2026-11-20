"""Root URL configuration for the Brewnook backend."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("invoices.urls")),
    path("api/", include("chat.urls")),
]
if settings.DEBUG:
    urlpatterns += [
        path(
            "chat-test/",
            TemplateView.as_view(
                template_name="chat/echo.html"
            ),
            name="chat-echo-test",
        ),
        path(
            "support-test/",
            TemplateView.as_view(template_name="chat/support.html"),
            name="support-test",
        ),
    ]