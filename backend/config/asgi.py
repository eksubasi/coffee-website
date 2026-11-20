import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.prod",
)

django_asgi_app = get_asgi_application()

from chat.middleware import ChatTicketMiddleware  # noqa: E402
from chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": OriginValidator(
            ChatTicketMiddleware(URLRouter(websocket_urlpatterns)),
            settings.CHAT_ALLOWED_ORIGINS,
        ),
    }
)