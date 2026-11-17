import asyncio

from channels.testing import WebsocketCommunicator

from .consumers import EchoConsumer


def test_echo_returns_messages_through_channel_layer():
    async def scenario():
        communicator = WebsocketCommunicator(
            EchoConsumer.as_asgi(),
            "/ws/echo/",
        )

        try:
            connected, _ = await communicator.connect()
            assert connected

            messages = [
                "Merhaba",
                "Türkçe: çğıöşü",
                "İkinci mesaj",
            ]

            for message in messages:
                await communicator.send_to(text_data=message)
                response = await communicator.receive_from()
                assert response == message
        finally:
            await communicator.disconnect()

    asyncio.run(scenario())