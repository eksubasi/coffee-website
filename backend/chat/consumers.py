from channels.generic.websocket import AsyncWebsocketConsumer
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation, Message
from .services import can_access, message_data
from accounts.models import User


class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            await self.channel_layer.send(
                self.channel_name,
                {
                    "type": "echo.message",
                    "text": text_data,
                },
            )

    async def echo_message(self, event):
        await self.send(text_data=event["text"])

class SupportConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["pk"]
        self.group_name = None

        if self.scope.get("ticket_conversation") != str(self.conversation_id):
            await self.close(code=4403)
            return

        if not await self.allowed():
            await self.close(code=4403)
            return

        self.group_name = f"support.{self.conversation_id.hex}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()
        await self.send_json(
            {"type": "history", "messages": await self.history()}
        )

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if bytes_data is not None:
            await self.send_json({"type": "error", "detail": "Text only."})
            return

        try:
            content = json.loads(text_data or "")
        except (TypeError, ValueError):
            await self.send_json({"type": "error", "detail": "Invalid JSON."})
            return

        await self.receive_json(content)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            await self.send_json({"type": "error", "detail": "Invalid message."})
            return

        text = content.get("text")
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 2000:
            await self.send_json(
                {"type": "error", "detail": "Text must be 1–2000 characters."}
            )
            return

        if not await self.allowed():
            await self.close(code=4403)
            return

        message = await self.save_message(text.strip())
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "support.message", "message": message},
        )

    async def support_message(self, event):
        if not await self.allowed():
            await self.close(code=4403)
            return

        await self.send_json(
            {"type": "message", "message": event["message"]}
        )

    @database_sync_to_async
    def allowed(self):
        user = self.scope["user"]

        if user.is_authenticated:
            user = User.objects.filter(
                pk=user.pk,
                is_active=True,
            ).first()

            if user is None:
                return False

            self.scope["user"] = user
        conversation = Conversation.objects.filter(
            pk=self.conversation_id
        ).first()

        return bool(
            conversation
            and can_access(
                conversation,
                self.scope["user"],
                self.scope.get("guest_key", ""),
            )
        )

    @database_sync_to_async
    def history(self):
        messages = list(
            Message.objects.filter(
                conversation_id=self.conversation_id
            ).order_by("-id")[:50]
        )
        return [message_data(message) for message in reversed(messages)]

    @database_sync_to_async
    def save_message(self, text):
        user = self.scope["user"]
        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender=user if user.is_authenticated else None,
            sender_role=user.role if user.is_authenticated else "guest",
            text=text,
        )
        return message_data(message)