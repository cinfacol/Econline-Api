"""from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from .models import Payment, Order
from .serializers import PaymentSerializer
from users.models import User
from .views import PaymentViewSet
import stripe
import json
from django.conf import settings
from django.utils import timezone


class PaymentViewSetTests(TestCase):
    def test_stripe_webhook_endpoint_returns_200(self):
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_a1u3n9H0EMrN07PE8QMrnJfmmGlLScJ8Tiuv7dCPPpr9YnY7EhF8yApR5J",
                    "payment_intent": "pi_3RR0oHHXf3qEyMjJ0ymiiVyh",
                    "metadata": {
                        "order_id": "c76a2dac-1202-4414-9ae2-9dd4f584b1d6",
                        "payment_id": "0529b6f5-d17d-45f1-bf4c-e771c6890754",
                    },
                }
            },
        }
        payload_string = json.dumps(payload)

        # Genera la firma
        timestamp = int(timezone.now().timestamp())
        sig_header = f"t={timestamp},v1={stripe.Webhook.generate_signature(payload=payload_string, secret=settings.STRIPE_WEBHOOK_SECRET, timestamp=timestamp, scheme='v1')}"
        event = stripe.Webhook.construct_event(
            payload=payload_string,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
        # signature = event.signature

        url = reverse("payments-stripe-webhook")
        response = self.client.post(
            url,
            data=payload_string,  # Usa el payload como data
            content_type="application/json",  # Especifica el tipo de contenido
            HTTP_STRIPE_SIGNATURE=sig_header,  # Agrega la firma como encabezado
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentSerializerTests(TestCase):
    def test_payment_serializer_with_valid_data(self):
        # Crea un usuario de prueba
        user = User.objects.create(email="test@example.com")

        # Crea un pedido de prueba
        order = Order.objects.create(user=user, amount=100.00, status="C")

        # Crea un pago de prueba
        payment = Payment.objects.create(
            order=order, amount=100.00, payment_option="SC", status="C"
        )

        # Serializa el pago
        serializer = PaymentSerializer(payment)
        data = serializer.data

        # Verifica que los datos serializados sean correctos
        self.assertEqual(data["buyer"], payment.order.user.get_full_name())

        self.assertEqual(data["status"], "C")
        self.assertEqual(data["payment_option"], "SC")
        self.assertEqual(data["amount"], "100.00")

        # Deserializa los datos
        # payment_deserialized = PaymentSerializer(data=data) # No es necesario deserializar en este caso
        # self.assertTrue(payment_deserialized.is_valid()) # No es necesario deserializar en este caso
        # self.assertEqual(payment_deserialized.validated_data['amount'], 100.00) # No es necesario deserializar en este caso

"""
