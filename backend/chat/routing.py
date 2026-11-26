from django.conf import settings
from django.urls import path
from .middleware import ChatTicketMiddleware

from .consumers import EchoConsumer, SupportConsumer

websocket_urlpatterns = [
    path(
        "ws/support/<uuid:pk>/",
        ChatTicketMiddleware(SupportConsumer.as_asgi()),
    ),
]

if settings.DEBUG:
    websocket_urlpatterns += [
        path("ws/echo/", EchoConsumer.as_asgi()),
    ]