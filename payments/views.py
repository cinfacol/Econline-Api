import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from orders.models import Order
from shipping.models import Shipping
from .models import Payment
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
from cart.models import Cart
import stripe
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("payment").all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes += [IsPaymentPending]
        return super().get_permissions()

    @action(detail=False, methods=["GET"])
    def calculate_total(self, request):
        """Calcula el total del pago incluyendo envío y descuentos"""
        try:
            # Obtener shipping_id del query params
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
            subtotal = cart.get_subtotal()
            shipping_cost = shipping.price
            discount = cart.get_discount()
            total_amount = subtotal + shipping_cost - discount

            response_data = {
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "discount": discount,
                "total_amount": total_amount,
                "currency": "USD",
                "shipping_method": shipping.name,
                "estimated_days": shipping.time_to_delivery,
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error calculating total: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_checkout_session(self, request):
        """Crea una sesión de checkout con Stripe"""
        try:
            cart = request.user.cart
            shipping_id = request.data.get("shipping_id")

            if not shipping_id:
                return Response(
                    {"error": "Shipping method is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shipping = get_object_or_404(Shipping, id=shipping_id)
            total = cart.get_total() + shipping.price

            # Generar transaction_id único
            transaction_id = (
                f"txn_{str(uuid.uuid4().hex[:12])}_{int(timezone.now().timestamp())}"
            )

            # Crear la orden primero
            order = Order.objects.create(
                user=request.user,
                amount=total,
                shipping=shipping,
                status="P",  # Pending
                transaction_id=transaction_id,
            )

            # Crear el pago
            payment = Payment.objects.create(
                order=order,
                payment_option=Payment.STRIPE,
                amount=total,
                status=Payment.PENDING,
            )

            # Crear sesión de Stripe con datos adicionales
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(total * 100),
                            "product_data": {
                                "name": f"Order #{order.id}",
                                "description": f"Payment for order {order.id}",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/order/cancelled",
                metadata={
                    "order_id": str(order.id),
                    "payment_id": str(payment.id),
                },
                expires_at=int(timezone.now().timestamp() + 3600),  # Expira en 1 hora
                customer_email=request.user.email,  # Pre-llenar el email
            )

            # Guardar el ID de sesión
            payment.stripe_session_id = checkout_session.id
            payment.save()

            return Response(
                {
                    "sessionId": checkout_session.id,
                    "payment_id": payment.id,
                    "checkout_url": checkout_session.url,  # Incluir la URL de checkout
                    "expires_at": checkout_session.expires_at,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def process(self, request, id=None):
        """Procesa el pago y verifica la sesión de Stripe"""
        try:
            payment = get_object_or_404(Payment, id=id)
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
                {"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
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
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
