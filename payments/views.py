# Standard Library
import uuid
import logging
from decimal import Decimal
import json

# Third-party
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import UserRateThrottle
import stripe

# Local/First-party
from config.celery import app as celery_app
from cart.models import Cart
from orders.models import Order, OrderItem
from shipping.models import Shipping
from shipping.services import ServientregaService
from .models import Payment, PaymentMethod, Subscription, Refund
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
from .webhooks import WebhookHandler

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

CHANNELS_AVAILABLE = True

STRIPE_CONFIG = {
    "api_key": settings.STRIPE_SECRET_KEY,
    "webhook_secret": settings.STRIPE_WEBHOOK_SECRET,
    "success_url": settings.PAYMENT_SUCCESS_URL,
    "cancel_url": settings.PAYMENT_CANCEL_URL,
}

WEBHOOK_HANDLERS = {
    "checkout.session.completed": handle_checkout_session_completed_task,
    "payment_intent.succeeded": handle_payment_intent_succeeded_task,
    "payment_intent.payment_failed": handle_payment_intent_payment_failed_task,
    "charge.refunded": handle_refund_succeeded_task,
    "customer.subscription.created": handle_subscription_created_task,
    "customer.subscription.updated": handle_subscription_updated_task,
    "customer.subscription.deleted": handle_subscription_deleted_task,
}


class StripeClient:
    def __init__(self, api_key):
        self.client = stripe
        self.client.api_key = api_key

    @classmethod
    def get_client(cls):
        return cls(settings.STRIPE_SECRET_KEY)


class PaymentService:
    def process_checkout(self, user, cart, shipping):
        with transaction.atomic():
            order = self.create_order(...)
            payment = self.create_payment(...)
            session = self.create_stripe_session(...)
            return session


class PaymentRateThrottle(UserRateThrottle):
    rate = "3/minute"


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related(
        "order", "user", "payment_method", "order__shipping", "order__user"
    ).prefetch_related("order__orderitem_set", "order__orderitem_set__inventory")
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    lookup_field = "id"
    search_fields = [
        "order__id",
        "user__email",
        "stripe_payment_intent_id",
        "paypal_transaction_id",
        "external_reference",
    ]
    ordering_fields = ["created_at", "amount", "status", "payment_method"]

    def get_permissions(self):
        if self.action == "stripe_webhook":
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

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
    @csrf_exempt
    def stripe_webhook(self, request):
        webhook_handler = WebhookHandler()
        try:
            sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
            if not sig_header:
                logger.error("No se encontró la firma de Stripe en los headers")
                return Response(
                    {"error": _("No Stripe signature found in headers")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = webhook_handler.process_webhook(request.body, sig_header)

            # Notificar a través de WebSocket si es necesario
            if result["status"] == "success":
                try:
                    # Decodificar el body y convertirlo a diccionario
                    event_data = json.loads(request.body.decode("utf-8"))
                    self.notify_payment_update(result["event_type"], event_data)
                except Exception as e:
                    logger.error(f"Error al enviar notificación WebSocket: {str(e)}")

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(f"Error de firma en webhook: {str(e)}")
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error inesperado en webhook: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def notify_payment_update(self, event_type: str, event_data: dict):
        if not CHANNELS_AVAILABLE:
            logger.warning(
                "No se pudo notificar la actualización: Channels no está disponible"
            )
            return

        try:
            channel_layer = get_channel_layer()

            # Extraer el user_id de los metadatos del evento
            user_id = None
            if event_type == "charge.succeeded":
                user_id = (
                    event_data.get("data", {})
                    .get("object", {})
                    .get("metadata", {})
                    .get("user_id")
                )
            elif event_type == "checkout.session.completed":
                user_id = (
                    event_data.get("data", {})
                    .get("object", {})
                    .get("metadata", {})
                    .get("user_id")
                )
            elif event_type == "payment_intent.succeeded":
                user_id = (
                    event_data.get("data", {})
                    .get("object", {})
                    .get("metadata", {})
                    .get("user_id")
                )

            if user_id:
                async_to_sync(channel_layer.group_send)(
                    f"payment_updates_{user_id}",
                    {
                        "type": "payment_update",
                        "data": {"event_type": event_type, "payment_data": event_data},
                    },
                )
            else:
                logger.warning(f"No se encontró user_id en el evento {event_type}")
        except Exception as e:
            logger.error(f"Error al enviar notificación WebSocket: {str(e)}")

    @action(detail=False, methods=["GET"])
    def payment_methods(self, request):
        cache_key = f"active_payment_methods_{request.user.id}"
        methods = cache.get(cache_key)
        if not methods:
            methods = PaymentMethod.objects.filter(is_active=True)
            cache.set(cache_key, methods, timeout=3600)
        serializer = PaymentMethodSerializer(
            methods, many=True, context={"request": request}
        )
        return Response({"payment_methods": serializer.data})

    @action(detail=True, methods=["POST"])
    def refund(self, request, id=None):
        payment = self.get_object()
        if payment.status != Payment.PaymentStatus.COMPLETED:
            return Response(
                {"error": _("Solo se pueden reembolsar pagos completados.")},
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
                {"error": _("Error al procesar reembolso")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["GET"])
    def calculate_total(self, request):
        try:
            shipping_id = request.query_params.get("shipping_id")
            coupon_id = request.query_params.get("coupon_id")
            
            cart, _ = Cart.objects.prefetch_related("items").get_or_create(
                user=request.user
            )
            if not cart.items.exists():
                return Response(
                    {"error": _("El carrito está vacío")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Si no hay shipping_id, obtener el método de envío por defecto
            if not shipping_id:
                default_shipping = (
                    Shipping.objects.filter(is_active=True)
                    .order_by("standard_shipping_cost")
                    .first()
                )
                if default_shipping:
                    shipping_id = default_shipping.id
                else:
                    return Response(
                        {"error": _("No hay métodos de envío disponibles")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            shipping = get_object_or_404(Shipping, id=shipping_id)
            subtotal = Decimal(str(cart.get_subtotal()))
            shipping_cost = Decimal(str(shipping.calculate_shipping_cost(subtotal)))
            
            # Aplicar cupón si se proporciona coupon_id
            discount = Decimal("0")
            if coupon_id:
                try:
                    from coupons.models import Coupon
                    coupon = Coupon.objects.get(id=coupon_id, is_active=True)
                    # Verificar si el cupón es válido para el subtotal actual
                    if not coupon.min_purchase_amount or subtotal >= coupon.min_purchase_amount:
                        # Calcular descuento basado en el tipo de cupón
                        if coupon.percentage_coupon:
                            # Cupón de porcentaje
                            discount = (subtotal * coupon.percentage_coupon.discount_percentage) / 100
                            # Aplicar máximo descuento si está configurado
                            if coupon.max_discount_amount:
                                discount = min(discount, coupon.max_discount_amount)
                        elif coupon.fixed_price_coupon:
                            # Cupón de monto fijo
                            discount = coupon.fixed_price_coupon.discount_price
                        
                        # Aplicar el cupón al carrito
                        cart.coupon = coupon
                        cart.save()
                    else:
                        # Limpiar cupón si no cumple el mínimo
                        cart.coupon = None
                        cart.save()
                except Coupon.DoesNotExist:
                    # Limpiar cupón si no existe
                    cart.coupon = None
                    cart.save()
            # Si no hay coupon_id, NO usar el descuento actual del carrito
            # Solo calcular el total sin descuentos de cupón
            
            total = subtotal + shipping_cost - discount

            # Obtener la dirección del usuario para la cotización de Servientrega
            user_address = request.user.address_set.filter(is_default=True).first()

            # Preparar datos para la cotización de Servientrega
            servientrega_data = None
            if user_address:
                try:
                    servientrega_service = ServientregaService()
                    servientrega_data = servientrega_service.cotizar_envio(
                        origen_codigo=settings.SERVIENTREGA_ORIGIN_CODE,
                        destino_codigo=user_address.postal_zip_code,
                        peso=Decimal(
                            "1.0"
                        ),  # Peso por defecto, ajustar según necesidad
                        valor_declarado=float(
                            str(subtotal)
                        ),  # Convertir a string primero para evitar problemas de precisión
                        tipo_servicio=shipping.service_type,
                    )
                except Exception as e:
                    logger.error(f"Error al cotizar con Servientrega: {str(e)}")
                    # Continuamos sin los datos de Servientrega

            response_data = {
                "subtotal": str(subtotal),
                "shipping_cost": str(shipping_cost),
                "discount": str(discount),
                "total_amount": str(total),
                "currency": settings.PAYMENT_CURRENCY,
                "shipping_method": {
                    "id": shipping.id,
                    "name": shipping.name,
                    "service_type": shipping.service_type,
                    "transport_type": shipping.transport_type,
                    "estimated_days": shipping.get_estimated_delivery_days(),
                    "is_free": shipping_cost == Decimal("0"),
                    "free_shipping_threshold": str(shipping.free_shipping_threshold),
                },
                "servientrega_quote": servientrega_data,
            }
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error calculating total: {str(e)}")
            return Response(
                {"error": _("Error al calcular el total.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _calculate_order_total(self, cart, shipping):
        """
        Calcula el total de la orden incluyendo subtotal, envío y descuentos.
        """
        try:
            # Obtener el subtotal del carrito y asegurarnos que sea Decimal
            subtotal = Decimal(str(cart.get_subtotal()))
            logger.info(f"Subtotal: {subtotal}")

            # Calcular el costo de envío basado en el subtotal y asegurarnos que sea Decimal
            shipping_cost = Decimal(str(shipping.calculate_shipping_cost(subtotal)))
            logger.info(f"Shipping cost: {shipping_cost}")

            # Obtener el descuento y asegurarnos que sea Decimal
            discount = Decimal(str(cart.get_discount()))
            logger.info(f"Discount: {discount}")

            # Calcular el total final
            total = subtotal + shipping_cost - discount
            logger.info(f"Total: {total}")

            # Validar que el total sea positivo
            if total < Decimal("0.00"):
                raise ValidationError(_("El total no puede ser negativo."))

            return total

        except (TypeError, ValueError) as e:
            logger.error(f"Error en conversión de tipos: {str(e)}")
            raise ValidationError(_("Error en el formato de los valores numéricos."))
        except Exception as e:
            logger.error(f"Error calculating order total: {str(e)}")
            raise ValidationError(_("Error al calcular el total de la orden."))

    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def create_checkout_session(self, request, id=None):
        """Crear sesión de checkout de Stripe"""
        try:
            logger.info("Iniciando creación de sesión de checkout")
            
            # Usar explícitamente el serializer correcto para este endpoint
            from .serializers import CheckoutSessionSerializer
            serializer = CheckoutSessionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Log de datos recibidos
            logger.info(f"Checkout data: {serializer.validated_data}")

            cart = self.get_user_cart(request.user)
            logger.info(f"Cart subtotal: {cart.get_subtotal()}")

            shipping = self.validate_checkout_request(
                cart, serializer.validated_data["shipping_id"]
            )
            logger.info(f"Shipping method: {shipping.name}")
            logger.info(f"Shipping threshold: {shipping.free_shipping_threshold}")

            total = self._calculate_order_total(cart, shipping)
            logger.info(f"Total calculated: {total}")

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
        except stripe.error.StripeError as e:
            logger.error("Stripe error in checkout: %s", str(e))
            return Response(
                {
                    "error": _(
                        "Error al procesar el pago. Por favor, inténtelo de nuevo."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except (ValidationError, ValueError, TypeError) as e:
            logger.error("Error en checkout: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def validate_checkout_request(self, cart, shipping_id):
        if not cart or not cart.items.exists():
            raise ValidationError(_("Cart is empty"))
        if not shipping_id:
            raise ValidationError(_("Shipping method is required"))
        try:
            shipping = Shipping.objects.get(id=shipping_id)
        except Shipping.DoesNotExist:
            raise ValidationError(_("Invalid shipping method"))
        return shipping

    def create_order(self, user, total, shipping, transaction_id):
        cart = self.get_user_cart(user)
        order = Order.objects.create(
            user=user,
            amount=total,
            shipping=shipping,
            status=Order.OrderStatus.PENDING,
            transaction_id=transaction_id,
            currency="USD",
        )

        # Crear OrderItems para cada CartItem
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                inventory=cart_item.inventory,
                name=cart_item.inventory.product.name,
                price=cart_item.inventory.store_price,
                count=cart_item.quantity,
            )

        return order

    def create_payment(
        self,
        order,
        total,
        payment_method,
        user,
        currency=None,
        tax_amount=0,
        discount_amount=0,
        **kwargs,
    ):
        # Validar monto mínimo y máximo
        min_amount = Decimal(str(settings.PAYMENT_MIN_AMOUNT))
        max_amount = Decimal(str(settings.PAYMENT_MAX_AMOUNT))

        if total < min_amount:
            raise ValidationError(f"El monto mínimo de pago es {min_amount}")
        if total > max_amount:
            raise ValidationError(f"El monto máximo de pago es {max_amount}")

        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=total,
            status=Payment.PaymentStatus.PENDING,
            payment_method=payment_method,
            currency=currency or settings.PAYMENT_CURRENCY,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            **kwargs,
        )
        return payment

    def create_stripe_session(self, order, payment, user_email):
        logger.info("Creando sesión de Stripe con los siguientes metadatos:")
        metadata = self._get_metadata(order, payment)
        logger.info(metadata)

        # Obtener la dirección por defecto del usuario
        default_address = order.user.address_set.filter(is_default=True).first()

        # Construir metadata enriquecida
        enhanced_metadata = {
            **metadata,
            "order_id": str(order.id),
            "transaction_id": order.transaction_id,
            "order_total": str(order.amount),
            "customer_name": f"{order.user.first_name} {order.user.last_name}",
            "customer_email": user_email,
        }

        # Configuración base de la sesión
        session_data = {
            "payment_method_types": ["card"],
            "line_items": self._get_line_items(order),
            "mode": "payment",
            "success_url": self._get_success_url(),
            "cancel_url": self._get_cancel_url(),
            "metadata": enhanced_metadata,
            "expires_at": self._get_expiration_time(),
            "customer_email": user_email,
            "customer_creation": "always",
            "locale": "es",
            "billing_address_collection": "auto",
            "payment_intent_data": {
                "description": f"Order #{order.id} - {order.transaction_id}",
                "receipt_email": user_email,
                "metadata": {
                    "order_id": str(order.id),
                    "payment_id": str(payment.id),
                    "transaction_id": order.transaction_id,
                    "customer_id": str(order.user.id),
                },
            },
        }

        # Agregar descuentos si existen
        discounts = self._get_discounts(order)
        if discounts:
            session_data["discounts"] = discounts

        # Agregar información de envío si existe dirección por defecto
        if default_address:
            session_data["payment_intent_data"]["shipping"] = {
                "name": f"{order.user.first_name} {order.user.last_name}",
                "address": {
                    "line1": default_address.address_line_1,
                    "line2": default_address.address_line_2 or "",
                    "city": default_address.city,
                    "state": default_address.state_province_region,
                    "postal_code": default_address.postal_zip_code,
                    "country": default_address.country_region,
                },
            }

        # Crear la sesión de Stripe
        try:
            session = stripe.checkout.Session.create(**session_data)

            # Actualizar el descriptor de la declaración después de crear la sesión
            if session.payment_intent:
                stripe.PaymentIntent.modify(
                    session.payment_intent,
                    statement_descriptor="ECONLINE STORE",
                    statement_descriptor_suffix=str(order.id)[:4],
                )

            return session
        except Exception as e:
            logger.error(f"Error creating Stripe session: {str(e)}")
            raise

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
        line_items = []

        # Si no hay items en la orden, crear un item genérico
        if not order.orderitem_set.exists():
            line_items.append(
                {
                    "price_data": {
                        "currency": order.currency.lower(),
                        "unit_amount": int(
                            float(str(order.amount)) * 100
                        ),  # Convertir a centavos
                        "product_data": {
                            "name": f"Order #{order.id}",
                            "description": f"Payment for order {order.id}",
                            "metadata": {
                                "order_id": str(order.id),
                                "payment_id": str(order.payments.first().id),
                                "transaction_id": order.transaction_id,
                            },
                        },
                    },
                    "quantity": 1,
                    "adjustable_quantity": {"enabled": False},
                }
            )
            return line_items

        # Calcular el subtotal original (sin descuento)
        original_subtotal = sum(
            Decimal(str(item.price)) * item.count 
            for item in order.orderitem_set.all()
        )
        
        # Calcular el descuento aplicado
        discount_amount = original_subtotal - order.amount
        
        # Si hay descuento, ajustar los precios proporcionalmente
        if discount_amount > 0:
            discount_ratio = order.amount / original_subtotal
            
            # Agregar cada producto con precio ajustado
            for item in order.orderitem_set.all():
                product_data = {
                    "name": item.name,
                    "description": f"Product from {order.user.username} (con descuento aplicado)",
                    "metadata": {
                        "product_id": str(item.inventory.id) if item.inventory else "N/A",
                        "order_id": str(order.id),
                        "payment_id": str(order.payments.first().id),
                        "transaction_id": order.transaction_id,
                        "original_price": str(item.price),
                        "discount_applied": "true",
                    },
                }

                # Añadir imágenes si están disponibles
                if item.inventory and hasattr(item.inventory, "media"):
                    images = [img.image.url for img in item.inventory.media.all()[:8]]
                    if images:
                        product_data["images"] = images

                # Ajustar el precio con el descuento
                adjusted_price = Decimal(str(item.price)) * discount_ratio
                price_in_cents = int(float(str(adjusted_price)) * 100)

                line_items.append(
                    {
                        "price_data": {
                            "currency": order.currency.lower(),
                            "unit_amount": price_in_cents,
                            "product_data": product_data,
                        },
                        "quantity": item.count,
                        "adjustable_quantity": {"enabled": False},
                        "tax_rates": [],
                    }
                )
        else:
            # Sin descuento, usar precios originales
            for item in order.orderitem_set.all():
                product_data = {
                    "name": item.name,
                    "description": f"Product from {order.user.username}",
                    "metadata": {
                        "product_id": str(item.inventory.id) if item.inventory else "N/A",
                        "order_id": str(order.id),
                        "payment_id": str(order.payments.first().id),
                        "transaction_id": order.transaction_id,
                    },
                }

                # Añadir imágenes si están disponibles
                if item.inventory and hasattr(item.inventory, "media"):
                    images = [img.image.url for img in item.inventory.media.all()[:8]]
                    if images:
                        product_data["images"] = images

                # Usar el precio original del producto
                price_in_cents = int(float(str(item.price)) * 100)

                line_items.append(
                    {
                        "price_data": {
                            "currency": order.currency.lower(),
                            "unit_amount": price_in_cents,
                            "product_data": product_data,
                        },
                        "quantity": item.count,
                        "adjustable_quantity": {"enabled": False},
                        "tax_rates": [],
                    }
                )

        return line_items

    def _get_discounts(self, order):
        """Obtener descuentos para la sesión de Stripe"""
        # Por ahora, no usamos descuentos de Stripe para evitar complejidad
        # El descuento se aplica directamente en los precios de los productos
        return []

    def _get_success_url(self):
        return (
            f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}"
        )

    def _get_cancel_url(self):
        return f"{settings.FRONTEND_URL}/order/cancelled"

    def _get_metadata(self, order, payment):
        return {
            # Información básica de la orden
            "order_id": str(order.id),
            "payment_id": str(payment.id),
            "transaction_id": order.transaction_id,
            "order_status": order.status,
            # Información del cliente
            "user_id": str(order.user.id),
            "user_email": order.user.email,
            "username": order.user.username,
            # Información de envío
            "shipping_method": order.shipping.name if order.shipping else "No shipping",
            "shipping_address": str(order.address) if order.address else "No address",
            "delivery_time": (
                order.shipping.time_to_delivery if order.shipping else "N/A"
            ),
            # Información del pago
            "payment_method": payment.payment_method,
            "currency": order.currency,
            "subtotal": str(order.amount),
            "shipping_cost": str(
                order.shipping.standard_shipping_cost if order.shipping else 0
            ),
            "tax_amount": str(payment.tax_amount),
            "discount_amount": str(payment.discount_amount),
            "total_amount": str(payment.amount),
            # Información del pedido
            "items_count": str(order.orderitem_set.count()),
            "items_total": str(sum(item.count for item in order.orderitem_set.all())),
            # Metadata del sistema
            "environment": (
                settings.ENVIRONMENT
                if hasattr(settings, "ENVIRONMENT")
                else "development"
            ),
            "api_version": (
                settings.API_VERSION if hasattr(settings, "API_VERSION") else "1.0"
            ),
            "created_at": order.created_at.isoformat(),
        }

    def _get_expiration_time(self):
        return int(timezone.now().timestamp() + int(settings.PAYMENT_SESSION_TIMEOUT))

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def process(self, request, id=None):
        payment = self._get_payment_or_404(id)
        self._validate_user_authorization(payment, request.user)

        # Primero verificar el estado en nuestra base de datos
        if payment.status == Payment.PaymentStatus.COMPLETED:
            return Response(
                {
                    "status": Payment.PaymentStatus.COMPLETED,
                    "status_display": payment.get_status_display(),
                    "message": _("Payment already completed"),
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order.id),
                    "paid_at": payment.paid_at,
                },
                status=status.HTTP_200_OK,
            )

        # Verificar si hay una sesión existente y si ha expirado
        if payment.stripe_session_id:
            try:
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                if session.payment_status == "paid":
                    # Si el pago está pagado en Stripe pero no en nuestra base de datos
                    payment.status = Payment.PaymentStatus.COMPLETED
                    payment.paid_at = timezone.now()
                    payment.save()

                    # Actualizar el estado de la orden
                    payment.order.status = Order.OrderStatus.COMPLETED
                    payment.order.save()

                    # Limpiar el carrito
                    cart = Cart.objects.filter(user=payment.order.user).first()
                    if cart:
                        cart.items.all().delete()

                    # Enviar email de éxito
                    if payment.order.user and payment.order.user.email:
                        send_payment_success_email_task.delay(payment.order.user.email)

                    return Response(
                        {
                            "status": Payment.PaymentStatus.COMPLETED,
                            "status_display": payment.get_status_display(),
                            "message": _("Payment completed"),
                            "payment_id": str(payment.id),
                            "order_id": str(payment.order.id),
                            "paid_at": payment.paid_at,
                        },
                        status=status.HTTP_200_OK,
                    )
                elif session.expires_at and session.expires_at < int(
                    timezone.now().timestamp()
                ):
                    # Si la sesión ha expirado, crear una nueva
                    logger.info(
                        f"Session {session.id} has expired, creating new session"
                    )
                    payment.stripe_session_id = None
                    payment.save()
            except stripe.error.StripeError as e:
                logger.error(f"Error retrieving session: {str(e)}")
                payment.stripe_session_id = None
                payment.save()

        # Si no hay sesión o la anterior expiró, crear una nueva
        if not payment.stripe_session_id:
            try:
                session = self.create_stripe_session(
                    payment.order, payment, request.user.email
                )
                payment.stripe_session_id = session.id
                payment.save()

                return Response(
                    {
                        "status": payment.status,
                        "status_display": payment.get_status_display(),
                        "message": _("New checkout session created"),
                        "payment_status": "unpaid",
                        "checkout_url": session.url,
                        "expires_at": session.expires_at,
                        "session_id": session.id,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                logger.error(f"Error creating Stripe session: {str(e)}")
                return Response(
                    {
                        "error": _("Error creating payment session"),
                        "message": str(e),
                        "status": payment.status,
                        "status_display": payment.get_status_display(),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Si hay una sesión válida, devolver su información
        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
            return Response(
                {
                    "status": payment.status,
                    "status_display": payment.get_status_display(),
                    "message": _("Payment is still pending"),
                    "payment_status": session.payment_status,
                    "checkout_url": session.url,
                    "expires_at": session.expires_at,
                    "session_id": session.id,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payment {payment.id}: {str(e)}")
            return Response(
                {
                    "error": _("Error processing payment"),
                    "message": str(e),
                    "status": payment.status,
                    "status_display": payment.get_status_display(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _get_payment_or_404(self, payment_id):
        return get_object_or_404(Payment.objects.select_related("order"), id=payment_id)

    def _validate_user_authorization(self, payment, user):
        if payment.order.user != user:
            return Response(
                {"error": _("No autorizado para procesar este pago")},
                status=status.HTTP_403_FORBIDDEN,
            )

    def _validate_stripe_session(self, payment):
        if not payment.stripe_session_id:
            return Response(
                {"error": _("Sesión de Stripe no encontrada")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _retrieve_stripe_session(self, session_id):
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Error retrieving Stripe session: {str(e)}")
            raise

    def _handle_payment_status(self, session, payment):
        handlers = {
            "paid": self._handle_successful_payment,
            "unpaid": self._handle_pending_payment,
            "open": self._handle_open_payment,
        }
        handler = handlers.get(session.payment_status, self._handle_failed_payment)
        return handler(session, payment)

    @transaction.atomic
    def _handle_successful_payment(self, session, payment):
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.paid_at = timezone.now()
        payment.save()

        self._update_order(payment.order)
        self._clear_cart(payment.order.user)
        self._send_success_email(payment.order.user)

        return Response(
            {
                "status": Payment.PaymentStatus.COMPLETED,
                "status_display": payment.get_status_display(),
                "message": _("Payment processed successfully"),
                "payment_id": str(payment.id),
                "order_id": str(payment.order.id),
            },
            status=status.HTTP_200_OK,
        )

    def _handle_pending_payment(self, session, payment):
        payment.status = Payment.PaymentStatus.PENDING
        payment.save()
        return Response(
            {
                "error": _("Payment is still pending"),
                "payment_status": session.payment_status,
                "checkout_url": session.url,
            },
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )

    def _handle_open_payment(self, session, payment):
        return Response(
            {
                "error": _("Payment is still open"),
                "payment_status": session.payment_status,
                "checkout_url": session.url,
            },
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )

    def _handle_failed_payment(self, session, payment):
        payment.status = Payment.PaymentStatus.FAILED
        payment.save()
        return Response(
            {
                "error": _("Payment failed"),
                "payment_status": session.payment_status,
                "retry_url": f"/api/payments/{payment.id}/retry_payment/",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _handle_stripe_error(self, payment, error):
        logger.error(f"Stripe error processing payment {payment.id}: {str(error)}")
        payment.status = Payment.PaymentStatus.FAILED
        payment.error_message = str(error)
        payment.save()

        return Response(
            {
                "error": _("Error procesando el pago"),
                "retry_url": f"/api/payments/{payment.id}/retry_payment/",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _update_order(self, order):
        order.status = order.OrderStatus.COMPLETED
        order.save()

    def _clear_cart(self, user):
        Cart.objects.filter(user=user).update(items=None)

    def _send_success_email(self, user):
        if user and user.email:
            send_payment_success_email_task.delay(
                user.email,
                from_email=settings.PAYMENT_EMAIL_FROM,
                subject=settings.PAYMENT_EMAIL_SUBJECT,
            )

    @action(detail=True, methods=["get"])
    def verify(self, request, id=None):
        payment = get_object_or_404(Payment, id=id)
        if payment.order.user != request.user:
            return Response(
                {"error": _("Payment not found")}, status=status.HTTP_404_NOT_FOUND
            )

        # Si el pago está completado, devolver información básica
        if payment.status == Payment.PaymentStatus.COMPLETED:
            return Response(
                {
                    "status": payment.status,
                    "status_display": payment.get_status_display(),
                    "payment_method": PaymentMethodSerializer(
                        payment.payment_method
                    ).data,
                    "paid_at": payment.paid_at,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "transaction_id": payment.order.transaction_id,
                    "order_id": str(payment.order.id),
                }
            )

        # Si el pago está pendiente, verificar en Stripe
        if payment.stripe_session_id:
            try:
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                return Response(
                    {
                        "status": payment.status,
                        "status_display": payment.get_status_display(),
                        "payment_method": PaymentMethodSerializer(
                            payment.payment_method
                        ).data,
                        "stripe_status": session.payment_status,
                        "checkout_url": (
                            session.url if session.payment_status == "unpaid" else None
                        ),
                        "transaction_id": payment.order.transaction_id,
                        "order_id": str(payment.order.id),
                    }
                )
            except stripe.error.StripeError:
                pass

        # Si no hay información de Stripe o hay error, devolver estado básico
        return Response(
            {
                "status": payment.status,
                "status_display": payment.get_status_display(),
                "payment_method": PaymentMethodSerializer(payment.payment_method).data,
                "transaction_id": payment.order.transaction_id,
                "order_id": str(payment.order.id),
            }
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def retry_payment(self, request, id=None):
        try:
            payment = get_object_or_404(Payment, id=id)
            if payment.order.user != request.user:
                return Response(
                    {"error": _("Payment not found")}, status=status.HTTP_404_NOT_FOUND
                )
            if payment.status != Payment.PaymentStatus.FAILED:
                return Response(
                    {"error": _("Only failed payments can be retried")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            checkout_session = self.create_stripe_session(
                payment.order, payment, request.user.email
            )

            payment.stripe_session_id = checkout_session.id
            payment.status = Payment.PaymentStatus.PENDING
            payment.save()

            return Response(
                self.format_checkout_response(checkout_session, payment),
                status=status.HTTP_200_OK,
            )
        except stripe.error.StripeError as e:
            logger.error("Stripe error in retry payment: %s", str(e))
            return Response(
                {
                    "error": _(
                        "Error al procesar el pago. Por favor, inténtelo de nuevo."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except (ValidationError, ValueError, TypeError) as e:
            logger.error("Error en retry payment: %s", str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Suscripciones
    @action(detail=False, methods=["POST"])
    def create_subscription(self, request):
        try:
            active_subscription = Subscription.objects.filter(
                user=request.user, status=Subscription.SubscriptionStatus.ACTIVE
            ).first()
            if active_subscription:
                return Response(
                    {"error": _("Ya tienes una suscripción activa")},
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

    def _get_or_create_order(self, validated_data):
        """Obtener o crear la orden basada en los datos validados"""
        cart = self.get_user_cart(self.request.user)
        logger.info(f"Cart subtotal: {cart.get_subtotal()}")
        
        shipping = self.validate_checkout_request(
            cart, validated_data["shipping_id"]
        )
        logger.info(f"Shipping method: {shipping.name}")
        
        # Usar los valores calculados del frontend si están disponibles
        if all(key in validated_data for key in ['total_amount', 'subtotal', 'shipping_cost', 'discount']):
            total = Decimal(str(validated_data['total_amount']))
            logger.info(f"Using frontend calculated total: {total}")
        else:
            # Fallback: calcular desde el carrito
            total = self._calculate_order_total(cart, shipping)
            logger.info(f"Using backend calculated total: {total}")
        
        # Aplicar cupón al carrito si se proporciona
        if validated_data.get('coupon_id'):
            try:
                from coupons.models import Coupon
                coupon = Coupon.objects.get(id=validated_data['coupon_id'], is_active=True)
                cart.coupon = coupon
                cart.save()
                logger.info(f"Applied coupon: {coupon.name}")
            except Coupon.DoesNotExist:
                logger.warning(f"Coupon {validated_data['coupon_id']} not found")
                cart.coupon = None
                cart.save()
        
        transaction_id = self.generate_transaction_id()
        logger.info(f"Generated transaction ID: {transaction_id}")
        
        order = self.create_order(self.request.user, total, shipping, transaction_id)
        logger.info(f"Created order: {order.id} with amount: {order.amount}")
        
        return order

    def _create_payment(self, order, validated_data):
        """Crear el pago para la orden"""
        payment = self.create_payment(
            order,
            order.amount,
            validated_data["payment_method_id"],
            user=self.request.user,
        )
        return payment
