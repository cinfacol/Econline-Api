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
from .models import Payment, Subscription
from cart.models import Cart
from .serializers import (
    PaymentSerializer,
    SubscriptionSerializer,
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
from .tasks import (
    handle_checkout_session_completed_task,
    handle_payment_intent_succeeded_task,
    handle_payment_intent_payment_failed_task,
    handle_refund_succeeded_task,
    handle_subscription_created_task,
    handle_subscription_updated_task,
    handle_subscription_deleted_task,
)
import logging
from config.celery import app as celery_app

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related(
        "order", "order__user", "order__shipping"
    ).all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]

    @action(detail=False, methods=["POST"])
    def stripe_webhook(self, request):
        """Manejador de webhooks mejorado"""
        WEBHOOK_HANDLERS = {
            "checkout.session.completed": handle_checkout_session_completed_task,
            "payment_intent.succeeded": handle_payment_intent_succeeded_task,
            "payment_intent.payment_failed": handle_payment_intent_payment_failed_task,
            "charge.refunded": handle_refund_succeeded_task,
            "customer.subscription.created": handle_subscription_created_task,
            "customer.subscription.updated": handle_subscription_updated_task,
            "customer.subscription.deleted": handle_subscription_deleted_task,
        }

        try:
            sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
            if not sig_header:
                logger.error("No se encontró la firma de Stripe en los headers")
                return Response(
                    {"error": "No Stripe signature found in headers"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.debug("Headers recibidos:")
            for key, value in request.META.items():
                if key.startswith("HTTP_"):
                    logger.debug(f"{key}: {value}")

            logger.debug(f"Payload recibido: {request.body.decode('utf-8')}")
            logger.debug(f"Stripe-Signature: {sig_header}")
            logger.debug(
                f"Webhook Secret configurado: {settings.STRIPE_WEBHOOK_SECRET[:5]}..."
            )

            try:
                event = stripe.Webhook.construct_event(
                    payload=request.body,
                    sig_header=sig_header,
                    secret=settings.STRIPE_WEBHOOK_SECRET,
                )
            except ValueError as e:
                logger.error(f"Error al parsear el payload: {str(e)}")
                return Response(
                    {"error": "Invalid payload format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except stripe.error.SignatureVerificationError as e:
                logger.error(
                    "Error de verificación de firma. Detalles:\n"
                    f"Signature Header: {sig_header}\n"
                    f"Error: {str(e)}"
                )
                return Response(
                    {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
                )

            handler = WEBHOOK_HANDLERS.get(event.type)
            if handler:
                handler.delay(event.data.object)
                logger.info(f"Webhook procesado exitosamente: {event.type}")
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Evento no manejado: {event.type}")
                return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                "Error inesperado en webhook:",
                exc_info=True,
                extra={
                    "headers": request.META,
                    "body_preview": request.body[:100] if request.body else None,
                },
            )
            return Response(
                {"error": "Error interno procesando webhook"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["GET"])
    def payment_methods(self, request):
        """Obtiene los métodos de pago guardados del cliente"""
        try:
            customer = stripe.Customer.retrieve(request.user.stripe_customer_id)
            payment_methods = stripe.PaymentMethod.list(
                customer=customer.id, type="card"
            )
            return Response(payment_methods.data)
        except Exception as e:
            logger.error(f"Error retrieving payment methods: {str(e)}")
            return Response(
                {"error": "Error al obtener métodos de pago"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["POST"])
    def attach_payment_method(self, request):
        """Añade un nuevo método de pago al cliente"""
        try:
            payment_method = stripe.PaymentMethod.attach(
                request.data["payment_method_id"],
                customer=request.user.stripe_customer_id,
            )
            return Response(payment_method)
        except Exception as e:
            logger.error(f"Error attaching payment method: {str(e)}")
            return Response(
                {"error": "Error al añadir método de pago"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["POST"])
    def refund(self, request, id=None):
        """Procesa el reembolso de un pago"""
        try:
            payment = self.get_object()
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent,
                reason=request.data.get("reason", "requested_by_customer"),
            )
            payment.status = Payment.PaymentStatus.REFUNDED
            payment.save()
            return Response(refund)
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return Response(
                {"error": "Error al procesar reembolso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

    """ @action(detail=False, methods=["get"])
    def client_token(self, request):
        # Genera un token para el cliente de Stripe
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
            ) """

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

    @action(detail=False, methods=["POST"])
    def create_subscription(self, request):
        """Crea una nueva suscripción"""
        try:
            # Verificar si ya existe una suscripción activa
            active_subscription = Subscription.objects.filter(
                user=request.user, status=Subscription.SubscriptionStatus.ACTIVE
            ).first()

            if active_subscription:
                return Response(
                    {"error": "Ya tienes una suscripción activa"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear o recuperar el cliente de Stripe
            if not request.user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email, source=request.data.get("token")
                )
                request.user.stripe_customer_id = customer.id
                request.user.save()

            # Crear la suscripción en Stripe
            stripe_subscription = stripe.Subscription.create(
                customer=request.user.stripe_customer_id,
                items=[{"price": request.data.get("price_id")}],
                expand=["latest_invoice.payment_intent"],
            )

            # Crear la suscripción en nuestra base de datos
            subscription = Subscription.objects.create(
                user=request.user,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=request.user.stripe_customer_id,
                stripe_price_id=request.data.get("price_id"),
                status=stripe_subscription.status.upper(),
                current_period_start=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                ),
            )

            return Response(SubscriptionSerializer(subscription).data)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def current_subscription(self, request):
        """Obtiene la suscripción actual del usuario"""
        subscription = Subscription.objects.filter(
            user=request.user, status=Subscription.SubscriptionStatus.ACTIVE
        ).first()

        if not subscription:
            return Response(
                {"error": "No tienes una suscripción activa"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SubscriptionSerializer(subscription).data)

    @action(detail=True, methods=["POST"])
    def cancel_subscription(self, request, id=None):
        """Cancela una suscripción"""
        try:
            subscription = get_object_or_404(Subscription, id=id, user=request.user)

            # Cancelar en Stripe
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id, cancel_at_period_end=True
            )

            # Actualizar en nuestra base de datos
            subscription.cancel_at_period_end = True
            subscription.canceled_at = timezone.now()
            subscription.save()

            return Response(SubscriptionSerializer(subscription).data)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
