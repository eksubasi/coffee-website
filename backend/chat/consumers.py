from channels.generic.websocket import AsyncWebsocketConsumer


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