from django.conf import settings
from django.urls import path

from .consumers import EchoConsumer, SupportConsumer

websocket_urlpatterns = [
    path("ws/support/<uuid:pk>/", SupportConsumer.as_asgi()),
]

if settings.DEBUG:
    websocket_urlpatterns += [
        path("ws/echo/", EchoConsumer.as_asgi()),
    ]