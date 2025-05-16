import uuid
import stripe
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from orders.models import Order
from shipping.models import Shipping
from .models import Payment
from cart.models import Cart
from .serializers import (
    PaymentSerializer,
    CheckoutSerializer,
    PaymentTotalSerializer,
    CheckoutSessionSerializer,
    PaymentVerificationSerializer,
)
from .permissions import (
    IsPaymentByUser,
    IsPaymentPending,
    IsPaymentForOrderNotCompleted,
    DoesOrderHaveAddress,
)
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("payment").all()

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]

    @action(detail=False, methods=["POST"], permission_classes=[permissions.AllowAny])
    def stripe_webhook(self, request):
        """
        Endpoint para recibir los webhooks de Stripe.
        """
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Received Stripe webhook event: {event.type}")

        # Handle the event
        if event.type == "checkout.session.completed":
            session = event.data.object
            self.handle_checkout_session_completed(session)

        elif event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            self.handle_payment_intent_succeeded(payment_intent)

        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            self.handle_payment_intent_payment_failed(payment_intent)

        # ... otros eventos ...

        return Response(status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes += [IsPaymentPending]
        return super().get_permissions()

    def handle_checkout_session_completed(self, session):
        """Maneja el evento checkout.session.completed"""
        try:
            payment_id = session.metadata.get("payment_id")
            payment = Payment.objects.get(id=payment_id)
            payment.status = payment.COMPLETED
            payment.save()

            order_id = session.metadata.get("order_id")
            order = Order.objects.get(id=order_id)
            order.status = "C"  # Completada
            order.save()

            # Limpiar el carrito después del pago exitoso
            cart = Cart.objects.filter(user=payment.order.user).first()
            if cart:
                cart.items.all().delete()

            logger.info(f"Checkout session completed for payment {payment_id}")

        except Payment.DoesNotExist:
            logger.error(f"Payment with id {payment_id} not found")
        except Order.DoesNotExist:
            logger.error(f"Order with id {order_id} not found")
        except Exception as e:
            logger.error(f"Error handling checkout.session.completed: {str(e)}")

    def handle_payment_intent_succeeded(self, payment_intent):
        """Maneja el evento payment_intent.succeeded"""
        try:
            payment_id = payment_intent.metadata.get("payment_id")
            payment = Payment.objects.get(id=payment_id)
            payment.status = Payment.COMPLETED
            payment.save()

            order_id = payment_intent.metadata.get("order_id")
            order = Order.objects.get(id=order_id)
            order.status = "C"  # Completada
            order.save()

            # Limpiar el carrito después del pago exitoso
            cart = Cart.objects.filter(user=payment.order.user).first()
            if cart:
                cart.items.all().delete()

            logger.info(f"Payment intent succeeded for payment {payment_id}")

        except Payment.DoesNotExist:
            logger.error(f"Payment with id {payment_id} not found")
        except Order.DoesNotExist:
            logger.error(f"Order with id {order_id} not found")
        except Exception as e:
            logger.error(f"Error handling payment_intent.succeeded: {str(e)}")

    def handle_payment_intent_payment_failed(self, payment_intent):
        """Maneja el evento payment_intent.payment_failed"""
        try:
            payment_id = payment_intent.metadata.get("payment_id")
            payment = Payment.objects.get(id=payment_id)
            payment.status = Payment.FAILED
            payment.save()

            order_id = payment_intent.metadata.get("order_id")
            order = Order.objects.get(id=order_id)
            order.status = "F"  # Fallida
            order.save()

            logger.warning(f"Payment intent failed for payment {payment_id}")

        except Payment.DoesNotExist:
            logger.error(f"Payment with id {payment_id} not found")
        except Order.DoesNotExist:
            logger.error(f"Order with id {order_id} not found")
        except Exception as e:
            logger.error(f"Error handling payment_intent.payment_failed: {str(e)}")

    @action(detail=False, methods=["GET"])
    def calculate_total(self, request):
        """Calcula el total del pago incluyendo envío y descuentos"""
        try:
            shipping_id = request.query_params.get("shipping_id")
            if not shipping_id:
                return Response(
                    {"error": "shipping_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Obtener o crear el carrito del usuario
            cart, _ = Cart.objects.prefetch_related("items").get_or_create(
                user=request.user
            )

            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener costo de envío
            shipping = get_object_or_404(Shipping, id=shipping_id)

            # Calcular totales
            total = self._calculate_order_total(cart, shipping)

            response_data = {
                "subtotal": cart.get_subtotal(),
                "shipping_cost": shipping.price,
                "discount": cart.get_discount(),
                "total_amount": total,
                "currency": "USD",
                "shipping_method": shipping.name,
                "estimated_days": shipping.time_to_delivery,
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error calculating total: {str(e)}")
            return Response(
                {"error": "Error al calcular el total."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _calculate_order_total(self, cart, shipping):
        """
        Método auxiliar para calcular el total del pedido
        """
        subtotal = cart.get_subtotal()
        shipping_cost = shipping.price
        discount = cart.get_discount()
        return subtotal + shipping_cost - discount

        # def get_order_total(self, cart, shipping):
        """Calcula el total del pedido"""
        # return self._calculate_order_total(cart, shipping)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def create_checkout_session(self, request):
        """Crea una sesión de checkout con Stripe"""
        try:
            cart = self.get_user_cart(request.user)
            shipping = self.validate_checkout_request(
                cart, request.data.get("shipping_id")
            )

            total = self._calculate_order_total(cart, shipping)
            transaction_id = self.generate_transaction_id()

            order = self.create_order(request.user, total, shipping, transaction_id)
            payment = self.create_payment(order, total)

            checkout_session = self.create_stripe_session(
                order, payment, request.user.email
            )

            # Guardar el ID de sesión
            payment.stripe_session_id = checkout_session.id
            payment.save()

            return Response(
                self.format_checkout_response(checkout_session, payment),
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.warning(f"Validation error in checkout: {str(e)}")
            return Response(
                {"error": "Error en la validación del checkout."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error in checkout: {str(e)}")
            return Response(
                {"error": "Error al procesar el pago. Por favor, inténtelo de nuevo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.error(f"Unexpected error in checkout: {str(e)}")
            return Response(
                {"error": "Ocurrió un error inesperado al procesar el pago."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def validate_checkout_request(self, cart, shipping_id):
        """Valida los datos de entrada para el checkout"""
        if not cart or not cart.items.exists():
            raise ValidationError("Cart is empty")

        if not shipping_id:
            raise ValidationError("Shipping method is required")

        try:
            shipping = Shipping.objects.get(id=shipping_id)
        except Shipping.DoesNotExist:
            raise ValidationError("Invalid shipping method")
        return shipping

    def create_order(self, user, total, shipping, transaction_id):
        """Crea una nueva orden"""
        return Order.objects.create(
            user=user,
            amount=total,
            shipping=shipping,
            status="C",
            transaction_id=transaction_id,
        )

    def create_payment(self, order, total):
        """Crea un nuevo pago"""
        return Payment.objects.create(
            order=order,
            payment_option=Payment.STRIPE,
            amount=total,
            status=Payment.PENDING,
        )

    def create_stripe_session(self, order, payment, user_email):
        """Crea una sesión de Stripe"""
        return stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=self._get_line_items(order),
            mode="payment",
            success_url=self._get_success_url(),
            cancel_url=self._get_cancel_url(),
            metadata=self._get_metadata(order, payment),
            expires_at=self._get_expiration_time(),
            customer_email=user_email,
        )

    def get_user_cart(self, user):
        """Obtiene el carrito del usuario"""
        cart = getattr(user, "cart", None)
        if not cart or not cart.items.exists():
            raise ValidationError("Cart is empty")
        cart = Cart.objects.prefetch_related("items").get(id=cart.id)
        return cart

        # def calculate_total(self, cart, shipping):
        """Calcula el total del pedido"""
        # return cart.get_total() + shipping.price

    def generate_transaction_id(self):
        """Genera un ID de transacción único"""
        timestamp = int(timezone.now().timestamp())
        unique_id = uuid.uuid4().hex[:12]
        return f"txn_{unique_id}_{timestamp}"

    def format_checkout_response(self, session, payment):
        """Formatea la respuesta del checkout"""
        return {
            "sessionId": session.id,
            "payment_id": payment.id,
            "checkout_url": session.url,
            "expires_at": session.expires_at,
            "amount": payment.amount,
            "currency": "USD",
        }

    def _get_line_items(self, order):
        """
        Obtiene los items para la sesión de Stripe
        """
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(
                        order.amount * 100
                    ),  # Stripe requiere el monto en centavos
                    "product_data": {
                        "name": f"Order #{order.id}",
                        "description": f"Payment for order {order.id}",
                    },
                },
                "quantity": 1,
            }
        ]

    def _get_success_url(self):
        """
        Obtiene la URL de éxito para la redirección
        """
        return (
            f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}"
        )

    def _get_cancel_url(self):
        """
        Obtiene la URL de cancelación para la redirección
        """
        return f"{settings.FRONTEND_URL}/order/cancelled"

    def _get_metadata(self, order, payment):
        """
        Obtiene los metadatos para la sesión de Stripe
        """
        return {
            "order_id": str(order.id),
            "payment_id": str(payment.id),
            "user_id": str(order.user.id),
        }

    def _get_expiration_time(self):
        """
        Obtiene el tiempo de expiración para la sesión
        """
        return int(timezone.now().timestamp() + 3600)  # 1 hora desde ahora

    @action(detail=True, methods=["post"])
    def process(self, request, id=None):
        """Procesa el pago y verifica la sesión de Stripe"""
        try:
            payment = get_object_or_404(Payment.objects.select_related("order"), id=id)
            logger.info(f"Processing payment {payment.id} with status {payment.status}")

            if payment.order.user != request.user:
                logger.warning(
                    f"User {request.user.id} attempted to access payment {payment.id}"
                )

                return Response(
                    {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if not payment.stripe_session_id:
                logger.error(f"No Stripe session found for payment {payment.id}")
                return Response(
                    {"error": "No Stripe session found for this payment"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                logger.info(
                    f"Retrieved Stripe session {session.id} with status {session.payment_status}"
                )
                print("session_paymen_status", session.payment_status)

                if session.payment_status == "paid":
                    payment.status = Payment.COMPLETED
                    payment.save()

                    order = payment.order
                    order.status = "C"
                    print("Order_status", order.status)
                    order.save()

                    # Limpiar el carrito después del pago exitoso
                    cart = Cart.objects.filter(user=request.user).first()
                    if cart:
                        cart.items.all().delete()

                    logger.info(f"Payment {payment.id} processed successfully")
                    return Response(
                        {
                            "status": "success",
                            "message": "Payment processed successfully",
                            "payment_id": str(payment.id),
                            "order_id": str(order.id),
                        }
                    )
                elif session.payment_status == "unpaid":
                    # El pago está pendiente o no se ha completado
                    payment.status = Payment.PENDING
                    payment.save()

                    return Response(
                        {
                            "error": "Payment is still pending",
                            "payment_status": session.payment_status,
                            "checkout_url": session.url,  # URL para completar el pago
                        },
                        status=status.HTTP_402_PAYMENT_REQUIRED,
                    )
                else:
                    payment.status = Payment.FAILED
                    payment.save()

                    logger.warning(
                        f"Payment {payment.id} failed with status {session.payment_status}"
                    )
                    return Response(
                        {
                            "error": "Payment failed",
                            "payment_status": session.payment_status,
                            "retry_url": f"/api/payments/{payment.id}/retry_payment/",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except stripe.error.InvalidRequestError as e:
                logger.error(f"Invalid Stripe session: {str(e)}")
                payment.status = Payment.FAILED
                payment.save()
                return Response(
                    {
                        "error": "Stripe session has expired. Please create a new checkout session.",
                        "retry_url": f"/api/payments/{payment.id}/retry_payment/",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response(
                {"error": "Error al procesar el pago. Por favor, inténtelo de nuevo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return Response(
                {"error": "Ocurrió un error inesperado al procesar el pago."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def verify(self, request, id=None):
        """Verifica el estado del pago"""
        payment = get_object_or_404(Payment, id=id)
        if payment.order.user != request.user:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {"status": payment.status, "payment_option": payment.payment_option}
        )

    @action(detail=False, methods=["get"])
    def client_token(self, request):
        """Genera un token para el cliente de Stripe"""
        try:
            # Aquí implementa la lógica para generar el token del cliente
            # usando tu proveedor de pagos (Stripe, PayPal, etc.)
            token = stripe.PaymentIntent.create(
                amount=1000,  # Monto mínimo o temporal
                currency="usd",
                setup_future_usage="off_session",
            )

            return Response({"token": token.client_secret})
        except Exception as e:
            return Response(
                {"error": "Error al calcular el total."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def retry_payment(self, request, id=None):
        """Reinicia un pago fallido"""
        try:
            payment = get_object_or_404(Payment, id=id)

            if payment.order.user != request.user:
                return Response(
                    {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if payment.status != Payment.FAILED:
                return Response(
                    {"error": "Only failed payments can be retried"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear nueva sesión de Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(payment.amount * 100),
                            "product_data": {
                                "name": f"Order #{payment.order.id}",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/order/cancelled",
                metadata={
                    "order_id": str(payment.order.id),
                    "payment_id": str(payment.id),
                },
            )

            # Actualizar payment con nueva sesión
            payment.stripe_session_id = checkout_session.id
            payment.status = Payment.PENDING
            payment.save()

            return Response(
                {"sessionId": checkout_session.id, "payment_id": payment.id},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error retrying payment: {str(e)}")
            return Response(
                {"error": "Error al calcular el total."},
                status=status.HTTP_400_BAD_REQUEST,
            )
