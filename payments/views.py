from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from shipping.models import Shipping
from .models import Payment
from .serializers import PaymentSerializer, CheckoutSerializer, PaymentTotalSerializer, CheckoutSessionSerializer, PaymentVerificationSerializer
from .permissions import (
    IsPaymentByUser,
    IsPaymentPending,
    IsPaymentForOrderNotCompleted,
    DoesOrderHaveAddress
)
from cart.models import Cart
import stripe
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('order').all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentByUser]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes += [IsPaymentPending]
        return super().get_permissions()


    @action(detail=False, methods=['GET'])
    def calculate_total(self, request):
        """Calcula el total del pago incluyendo envío y descuentos"""
        try:
            # Obtener shipping_id del query params
            shipping_id = request.query_params.get('shipping_id')
            if not shipping_id:
                return Response(
                    {"error": "shipping_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener o crear el carrito del usuario
            cart, _ = Cart.objects.prefetch_related('items').get_or_create(
                user=request.user
            )

            if not cart.items.exists():
                return Response(
                    {"error": "Cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST
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
                "estimated_days": shipping.time_to_delivery
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error calculating total: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def create_checkout_session(self, request):
        """Crea una sesión de checkout con Stripe"""
        try:
            cart = request.user.cart
            shipping_id = request.data.get('shipping_id')

            if not shipping_id:
                return Response(
                    {"error": "Shipping method is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            shipping = get_object_or_404(Shipping, id=shipping_id)
            total = cart.get_total() + shipping.price

            # Crear la orden primero
            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                shipping_method=shipping,
                status='P'  # Pending
            )

            # Crear el pago
            payment = Payment.objects.create(
                order=order,
                payment_option=Payment.STRIPE,
                amount=total,
                status=Payment.PENDING
            )

            # Crear sesión de Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(total * 100),
                        'product_data': {
                            'name': f'Order #{order.id}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/order/cancelled",
                metadata={
                    'order_id': str(order.id),
                    'payment_id': str(payment.id)
                }
            )

            # Guardar el ID de sesión
            payment.stripe_session_id = checkout_session.id
            payment.save()

            return Response({
                'sessionId': checkout_session.id,
                'payment_id': payment.id
            })

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Procesa el pago"""
        payment = self.get_object()

        try:
            if payment.payment_option == Payment.STRIPE:
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                if session.payment_status == 'paid':
                    payment.status = Payment.COMPLETED
                    payment.save()

                    # Actualizar estado de la orden
                    order = payment.order
                    order.status = 'C'  # Completed
                    order.save()

                    return Response({'status': 'success'})
                else:
                    payment.status = Payment.FAILED
                    payment.save()
                    return Response(
                        {'error': 'Payment failed'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        """Verifica el estado del pago"""
        payment = self.get_object()
        return Response({
            'status': payment.status,
            'payment_option': payment.payment_option
        })

    @action(detail=False, methods=['get'])
    def client_token(self, request):
        """Genera un token para el cliente de Stripe"""
        try:
            # Aquí implementa la lógica para generar el token del cliente
            # usando tu proveedor de pagos (Stripe, PayPal, etc.)
            token = stripe.PaymentIntent.create(
                amount=1000,  # Monto mínimo o temporal
                currency='usd',
                setup_future_usage='off_session',
            )

            return Response({
                'token': token.client_secret
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
