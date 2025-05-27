import uuid
import stripe
import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from orders.models import Order
from shipping.models import Shipping
from .models import Payment, PaymentMethod, Subscription, Refund
from cart.models import Cart
from .serializers import (
    PaymentSerializer,
    PaymentMethodSerializer,
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
    send_payment_success_email_task,
    send_subscription_welcome_email,
    send_subscription_canceled_email,
)
from config.celery import app as celery_app

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_session_completed_task,
    "payment_intent.succeeded": handle_payment_intent_succeeded_task,
    "payment_intent.payment_failed": handle_payment_intent_payment_failed_task,
    "charge.refunded": handle_refund_succeeded_task,
    "customer.subscription.created": handle_subscription_created_task,
    "customer.subscription.updated": handle_subscription_updated_task,
    "customer.subscription.deleted": handle_subscription_deleted_task,
}


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related(
        "order", "user", "payment_method", "order__shipping"
    ).all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "order__id",
        "user__email",
        "stripe_payment_intent_id",
        "paypal_transaction_id",
        "external_reference",
    ]
    ordering_fields = ["created_at", "amount", "status", "payment_method"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        payment_method_id = self.request.query_params.get("payment_method_id")
        if payment_method_id:
            qs = qs.filter(payment_method_id=payment_method_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["POST"])
    def stripe_webhook(self, request):
        try:
            sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
            if not sig_header:
                logger.error("No se encontró la firma de Stripe en los headers")
                return Response(
                    {"error": "No Stripe signature found in headers"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            event = stripe.Webhook.construct_event(
                payload=request.body,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET,
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
            logger.error("Error inesperado en webhook:", exc_info=True)
            return Response(
                {"error": "Error interno procesando webhook"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["GET"])
    def payment_methods(self, request):
        methods = PaymentMethod.objects.filter(is_active=True)
        serializer = PaymentMethodSerializer(
            methods, many=True, context={"request": request}
        )

        return Response({"payment_methods": serializer.data})

    @action(detail=True, methods=["POST"])
    def refund(self, request, id=None):
        payment = self.get_object()
        if payment.status != Payment.PaymentStatus.COMPLETED:
            return Response(
                {"error": "Solo se pueden reembolsar pagos completados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                reason=request.data.get("reason", "requested_by_customer"),
            )
            payment.status = Payment.PaymentStatus.REFUNDED
            payment.save()
            Refund.objects.create(
                payment=payment,
                user=request.user,
                amount=payment.amount,
                currency=payment.currency,
                stripe_refund_id=refund.id,
                reason=request.data.get("reason", "requested_by_customer"),
                status="succeeded",
            )
            return Response(refund)
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return Response(
                {"error": "Error al procesar reembolso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["GET"])
    def calculate_total(self, request):
        try:
            shipping_id = request.query_params.get("shipping_id")
            if not shipping_id:
                return Response(
                    {"error": "shipping_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart, _ = Cart.objects.prefetch_related("items").get_or_create(
                user=request.user
            )
            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )
            shipping = get_object_or_404(Shipping, id=shipping_id)
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
        subtotal = cart.get_subtotal()
        shipping_cost = shipping.price
        discount = cart.get_discount()
        return subtotal + shipping_cost - discount

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def create_checkout_session(self, request, id=None):
        try:
            serializer = CheckoutSessionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            cart = self.get_user_cart(request.user)
            shipping = self.validate_checkout_request(
                cart, serializer.validated_data["shipping_id"]
            )
            total = self._calculate_order_total(cart, shipping)
            transaction_id = self.generate_transaction_id()
            order = self.create_order(request.user, total, shipping, transaction_id)
            payment = self.create_payment(
                order,
                total,
                serializer.validated_data["payment_method_id"],
                user=request.user,
            )
            checkout_session = self.create_stripe_session(
                order, payment, request.user.email
            )
            payment.stripe_session_id = checkout_session.id
            payment.save()
            return Response(
                self.format_checkout_response(checkout_session, payment),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error en checkout: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error in checkout: {str(e)}")
            return Response(
                {"error": "Error al procesar el pago. Por favor, inténtelo de nuevo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

    def validate_checkout_request(self, cart, shipping_id):
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
        return Order.objects.create(
            user=user,
            amount=total,
            shipping=shipping,
            status="C",
            transaction_id=transaction_id,
        )

    def create_payment(
        self,
        order,
        total,
        payment_method,
        user,
        currency="USD",
        tax_amount=0,
        discount_amount=0,
        **kwargs,
    ):
        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=total,
            status=Payment.PaymentStatus.PENDING,
            payment_method=payment_method,
            currency=currency,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            **kwargs,
        )
        print(f"Payment creado: {payment}, status: {payment.status}")
        return payment

    def create_stripe_session(self, order, payment, user_email):
        logger.info("Creando sesión de Stripe con los siguientes metadatos:")
        logger.info(self._get_metadata(order, payment))
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
        cart = getattr(user, "cart", None)
        if not cart or not cart.items.exists():
            raise ValidationError("Cart is empty")
        cart = Cart.objects.prefetch_related("items").get(id=cart.id)
        return cart

    def generate_transaction_id(self):
        timestamp = int(timezone.now().timestamp())
        unique_id = uuid.uuid4().hex[:12]
        return f"txn_{unique_id}_{timestamp}"

    def format_checkout_response(self, session, payment):
        return {
            "sessionId": session.id,
            "payment_id": payment.id,
            "checkout_url": session.url,
            "expires_at": session.expires_at,
            "amount": payment.amount,
            "currency": payment.currency,
        }

    def _get_line_items(self, order):
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(order.amount * 100),
                    "product_data": {
                        "name": f"Order #{order.id}",
                        "description": f"Payment for order {order.id}",
                    },
                },
                "quantity": 1,
            }
        ]

    def _get_success_url(self):
        return (
            f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}"
        )

    def _get_cancel_url(self):
        return f"{settings.FRONTEND_URL}/order/cancelled"

    def _get_metadata(self, order, payment):
        return {
            "order_id": str(order.id),
            "payment_id": str(payment.id),
            "user_id": str(order.user.id),
        }

    def _get_expiration_time(self):
        return int(timezone.now().timestamp() + 3600)  # 1 hora desde ahora

    @action(detail=True, methods=["post"])
    def process(self, request, id=None):
        payment = get_object_or_404(Payment.objects.select_related("order"), id=id)
        if payment.order.user != request.user:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if not payment.stripe_session_id:
            return Response(
                {"error": "No Stripe session found for this payment"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
            if session.payment_status == "paid":
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.save()
                order = payment.order
                order.status = "C"
                order.save()
                cart = Cart.objects.filter(user=request.user).first()
                if cart:
                    cart.items.all().delete()
                # Enviar email de éxito de pago
                if payment.order.user and payment.order.user.email:
                    send_payment_success_email_task.delay(payment.order.user.email)
                return Response(
                    {
                        "status": "success",
                        "message": "Payment processed successfully",
                        "payment_id": str(payment.id),
                        "order_id": str(order.id),
                    }
                )
            elif session.payment_status == "unpaid":
                payment.status = Payment.PaymentStatus.PENDING
                payment.save()
                return Response(
                    {
                        "error": "Payment is still pending",
                        "payment_status": session.payment_status,
                        "checkout_url": session.url,
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
            elif session.payment_status == "open":
                return Response(
                    {
                        "error": "Payment is still open",
                        "payment_status": session.payment_status,
                        "checkout_url": session.url,
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
            else:
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                return Response(
                    {
                        "error": "Payment failed",
                        "payment_status": session.payment_status,
                        "retry_url": f"/api/payments/{payment.id}/retry_payment/",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except stripe.error.InvalidRequestError as e:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()
            return Response(
                {
                    "error": "Stripe session has expired. Please create a new checkout session.",
                    "retry_url": f"/api/payments/{payment.id}/retry_payment/",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def verify(self, request, id=None):
        payment = get_object_or_404(Payment, id=id)
        if payment.order.user != request.user:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {
                "status": payment.status,
                "payment_method": PaymentMethodSerializer(payment.payment_method).data,
            }
        )

    @action(detail=True, methods=["post"])
    def retry_payment(self, request, id=None):
        payment = get_object_or_404(Payment, id=id)
        if payment.order.user != request.user:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if payment.status != Payment.PaymentStatus.FAILED:
            return Response(
                {"error": "Only failed payments can be retried"},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        payment.stripe_session_id = checkout_session.id
        payment.status = Payment.PaymentStatus.PENDING
        payment.save()
        return Response(
            {"sessionId": checkout_session.id, "payment_id": payment.id},
            status=status.HTTP_200_OK,
        )

    # Suscripciones
    @action(detail=False, methods=["POST"])
    def create_subscription(self, request):
        try:
            active_subscription = Subscription.objects.filter(
                user=request.user, status=Subscription.SubscriptionStatus.ACTIVE
            ).first()
            if active_subscription:
                return Response(
                    {"error": "Ya tienes una suscripción activa"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not request.user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email, source=request.data.get("token")
                )
                request.user.stripe_customer_id = customer.id
                request.user.save()
            stripe_subscription = stripe.Subscription.create(
                customer=request.user.stripe_customer_id,
                items=[{"price": request.data.get("price_id")}],
                expand=["latest_invoice.payment_intent"],
            )
            subscription = Subscription.objects.create(
                user=request.user,
                stripe_subscription_id=stripe_subscription.id,
                status=stripe_subscription.status.upper(),
                current_period_start=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=timezone.datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                ),
            )
            # Enviar email de bienvenida
            if subscription.user and subscription.user.email:
                send_subscription_welcome_email.delay(subscription.user.email)
            return Response(SubscriptionSerializer(subscription).data)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def current_subscription(self, request):
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
        try:
            subscription = get_object_or_404(Subscription, id=id, user=request.user)
            stripe.Subscription.modify(
                subscription.stripe_subscription_id, cancel_at_period_end=True
            )
            subscription.cancel_at_period_end = True
            subscription.canceled_at = timezone.now()
            subscription.save()
            # Enviar email de cancelación
            if subscription.user and subscription.user.email:
                send_subscription_canceled_email.delay(
                    subscription.user.email, end_date=subscription.current_period_end
                )
            return Response(SubscriptionSerializer(subscription).data)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
