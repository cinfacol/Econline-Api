from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import stripe
from unittest.mock import patch, MagicMock

from payments.models import Payment, PaymentMethod
from orders.models import Order
from cart.models import Cart
from shipping.models import Shipping

User = get_user_model()


class PaymentCancellationFlowTest(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear método de pago
        self.payment_method = PaymentMethod.objects.create(
            key='SC',
            label='Stripe Card',
            is_active=True
        )
        
        # Crear método de envío
        self.shipping = Shipping.objects.create(
            name='Test Shipping',
            standard_shipping_cost=Decimal('5.00'),
            is_active=True
        )
        
        # Crear carrito
        self.cart = Cart.objects.create(user=self.user)
        
        # Crear orden
        self.order = Order.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            shipping=self.shipping,
            status=Order.OrderStatus.PENDING,
            transaction_id='test_txn_123'
        )
        
        # Crear pago
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            amount=Decimal('100.00'),
            status=Payment.PaymentStatus.PENDING,
            payment_method=self.payment_method,
            stripe_session_id='cs_test_session_123'
        )

    @patch('stripe.checkout.Session.retrieve')
    @patch('stripe.PaymentIntent.cancel')
    def test_manual_cancellation_success(self, mock_cancel, mock_retrieve):
        """Prueba la cancelación manual exitosa"""
        # Mock de la sesión de Stripe
        mock_session = MagicMock()
        mock_session.payment_intent = 'pi_test_123'
        mock_session.status = 'open'
        mock_retrieve.return_value = mock_session
        
        # Mock de la cancelación de PaymentIntent
        mock_cancel.return_value = MagicMock()
        
        # Simular cancelación
        from payments.tasks import handle_manual_payment_cancellation_task
        
        # Ejecutar la tarea
        handle_manual_payment_cancellation_task(str(self.payment.id), str(self.user.id), "test_cancellation")
        
        # Refrescar objetos desde la base de datos
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        
        # Verificar que el estado se actualizó correctamente
        self.assertEqual(self.payment.status, Payment.PaymentStatus.CANCELLED)
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)
        self.assertIn("test_cancellation", self.payment.error_message)

    @patch('stripe.checkout.Session.retrieve')
    def test_session_expiration_handling(self, mock_retrieve):
        """Prueba el manejo de sesiones expiradas"""
        # Mock de sesión expirada
        mock_session = MagicMock()
        mock_session.expires_at = int(timezone.now().timestamp()) - 3600  # 1 hora atrás
        mock_session.status = 'expired'
        mock_session.to_dict.return_value = {
            'id': 'cs_test_session_123',
            'metadata': {
                'payment_id': str(self.payment.id),
                'order_id': str(self.order.id)
            }
        }
        mock_retrieve.return_value = mock_session
        
        # Ejecutar la tarea de expiración
        from payments.tasks import handle_checkout_session_expired_task
        handle_checkout_session_expired_task(mock_session.to_dict())
        
        # Refrescar objetos
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        
        # Verificar que se canceló correctamente
        self.assertEqual(self.payment.status, Payment.PaymentStatus.CANCELLED)
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)
        self.assertIn("Sesión de checkout expirada", self.payment.error_message)

    def test_cancellation_of_completed_payment(self):
        """Prueba que no se puede cancelar un pago ya completado"""
        # Marcar pago como completado
        self.payment.status = Payment.PaymentStatus.COMPLETED
        self.payment.save()
        
        # Intentar cancelar
        from payments.tasks import handle_manual_payment_cancellation_task
        
        # La tarea debería manejar esto graciosamente
        handle_manual_payment_cancellation_task(str(self.payment.id), str(self.user.id), "test_cancellation")
        
        # Refrescar
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        
        # El estado debería permanecer como COMPLETED
        self.assertEqual(self.payment.status, Payment.PaymentStatus.COMPLETED)
        self.assertEqual(self.order.status, Order.OrderStatus.PENDING)  # No debería cambiar

    @patch('stripe.checkout.Session.retrieve')
    def test_session_not_found_in_stripe(self, mock_retrieve):
        """Prueba el manejo cuando la sesión no existe en Stripe"""
        # Mock de error de sesión no encontrada
        mock_retrieve.side_effect = stripe.error.InvalidRequestError("No such session", "cs_test_session_123")
        
        # Ejecutar la tarea de expiración
        from payments.tasks import handle_checkout_session_expired_task
        
        session_data = {
            'id': 'cs_test_session_123',
            'metadata': {
                'payment_id': str(self.payment.id),
                'order_id': str(self.order.id)
            }
        }
        
        # Esto debería manejar el error y cancelar el pago
        from payments.tasks import handle_manual_payment_cancellation_task
        handle_manual_payment_cancellation_task(str(self.payment.id), str(self.user.id), "sesión_no_encontrada_en_stripe")
        
        # Refrescar
        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        
        # Verificar que se canceló
        self.assertEqual(self.payment.status, Payment.PaymentStatus.CANCELLED)
        self.assertEqual(self.order.status, Order.OrderStatus.CANCELLED)

    def test_periodic_clean_task(self):
        """Prueba la tarea periódica de limpieza"""
        # Crear varios pagos pendientes
        payment2 = Payment.objects.create(
            order=self.order,
            user=self.user,
            amount=Decimal('50.00'),
            status=Payment.PaymentStatus.PENDING,
            payment_method=self.payment_method,
            stripe_session_id='cs_test_session_456'
        )
        
        # Mock de la verificación de sesiones
        with patch('stripe.checkout.Session.retrieve') as mock_retrieve:
            # Simular que la primera sesión está expirada
            mock_session1 = MagicMock()
            mock_session1.expires_at = int(timezone.now().timestamp()) - 3600
            mock_session1.to_dict.return_value = {
                'id': 'cs_test_session_123',
                'metadata': {'payment_id': str(self.payment.id), 'order_id': str(self.order.id)}
            }
            
            # Simular que la segunda sesión no existe
            mock_retrieve.side_effect = [
                mock_session1,  # Primera llamada
                stripe.error.InvalidRequestError("No such session", "cs_test_session_456")  # Segunda llamada
            ]
            
            # Ejecutar la tarea periódica
            from payments.tasks import periodic_clean_expired_sessions_task
            result = periodic_clean_expired_sessions_task()
            
            # Verificar el resultado
            self.assertEqual(result['expired_count'], 2)
            self.assertEqual(result['total_checked'], 2)

    def test_cart_coupons_clearing(self):
        """Prueba que se limpian los cupones del carrito al cancelar"""
        # Simular que el carrito tiene cupones
        from coupons.models import Coupon
        
        # Crear un cupón de prueba
        coupon = Coupon.objects.create(
            name='TEST_COUPON',
            code='TEST10',
            is_active=True
        )
        
        # Agregar cupón al carrito
        self.cart.coupons.add(coupon)
        self.assertEqual(self.cart.coupons.count(), 1)
        
        # Cancelar el pago
        from payments.tasks import handle_manual_payment_cancellation_task
        handle_manual_payment_cancellation_task(str(self.payment.id), str(self.user.id), "test_cancellation")
        
        # Refrescar carrito
        self.cart.refresh_from_db()
        
        # Verificar que se limpiaron los cupones
        self.assertEqual(self.cart.coupons.count(), 0) 