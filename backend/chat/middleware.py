from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import signing


@database_sync_to_async
def ticket_user(user_id):
    if user_id is None:
        return AnonymousUser()

    return get_user_model().objects.filter(
        pk=user_id,
        is_active=True,
    ).first()


class ChatTicketMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope = dict(scope)

        try:
            query = parse_qs(scope.get("query_string", b"").decode())
            ticket = query.get("ticket", [""])[0]
            identity = signing.loads(
                ticket,
                salt="chat.websocket",
                max_age=60,
            )
            if not isinstance(identity, dict):
                raise ValueError("Invalid chat ticket payload.")
        except (signing.BadSignature, ValueError, UnicodeDecodeError):
            await send({"type": "websocket.close", "code": 4401})
            return

        user = await ticket_user(identity.get("user_id"))
        if user is None:
            await send({"type": "websocket.close", "code": 4401})
            return

        scope["user"] = user
        scope["guest_key"] = identity.get("guest_key", "")
        scope["ticket_conversation"] = identity.get("conversation_id")

        return await self.app(scope, receive, send)