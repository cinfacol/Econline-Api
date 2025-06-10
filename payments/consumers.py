# payments/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Payment


class PaymentStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        self.room_group_name = f"payment_updates_{self.user_id}"

        # Unirse al grupo de WebSocket
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Abandonar el grupo de WebSocket
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        payment_id = text_data_json.get("payment_id")

        # Obtener el estado actual del pago
        payment_status = await self.get_payment_status(payment_id)
        await self.send(text_data=json.dumps(payment_status))

    async def payment_update(self, event):
        # Enviar actualización al WebSocket
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def get_payment_status(self, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, user_id=self.user_id)
            return {
                "status": payment.status,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "updated_at": payment.updated_at.isoformat(),
            }
        except Payment.DoesNotExist:
            return {"error": "Payment not found"}
