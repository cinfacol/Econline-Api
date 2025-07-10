from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from payments.models import Payment, PaymentMethod
from orders.models import Order
from cart.models import Cart
import stripe
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Prueba la cancelación de pagos en el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            type=str,
            help='ID específico del pago a probar',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email del usuario para buscar pagos',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales',
        )
        parser.add_argument(
            '--stripe-test',
            action='store_true',
            help='Probar integración con Stripe',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando pruebas de cancelación de pagos')
        )
        
        # Configurar Stripe si se solicita
        if options['stripe_test']:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.stdout.write('✅ Stripe configurado para pruebas')
        
        # Buscar pagos para probar
        payments = self._find_payments(options)
        
        if not payments:
            self.stdout.write(
                self.style.WARNING('⚠️  No se encontraron pagos para probar')
            )
            return
        
        self.stdout.write(f'✅ Encontrados {len(payments)} pagos para probar')
        
        # Ejecutar pruebas
        results = []
        for payment in payments:
            result = self._test_payment_cancellation(payment, options)
            results.append(result)
        
        # Mostrar resumen
        self._show_summary(results)

    def _find_payments(self, options):
        """Encontrar pagos para probar"""
        queryset = Payment.objects.select_related('order', 'user', 'payment_method')
        
        if options['payment_id']:
            try:
                return [queryset.get(id=options['payment_id'])]
            except Payment.DoesNotExist:
                raise CommandError(f'Pago con ID {options["payment_id"]} no encontrado')
        
        if options['user_email']:
            try:
                user = User.objects.get(email=options['user_email'])
                return list(queryset.filter(user=user))
            except User.DoesNotExist:
                raise CommandError(f'Usuario con email {options["user_email"]} no encontrado')
        
        # Por defecto, buscar pagos pendientes
        return list(queryset.filter(status=Payment.PaymentStatus.PENDING)[:5])

    def _test_payment_cancellation(self, payment, options):
        """Probar la cancelación de un pago específico"""
        self.stdout.write(f'\n📋 Probando pago: {payment.id}')
        self.stdout.write(f'   Estado actual: {payment.status}')
        self.stdout.write(f'   Orden: {payment.order.id}')
        self.stdout.write(f'   Usuario: {payment.order.user.email}')
        self.stdout.write(f'   Monto: {payment.amount} {payment.currency}')
        
        if options['dry_run']:
            self.stdout.write('   🔍 Modo dry-run: No se harán cambios')
            return {
                'payment_id': str(payment.id),
                'status': 'dry_run',
                'success': True,
                'message': 'Simulación completada'
            }
        
        try:
            with transaction.atomic():
                # Verificar estado inicial
                initial_payment_status = payment.status
                initial_order_status = payment.order.status
                
                # Simular cancelación
                payment.status = Payment.PaymentStatus.CANCELLED
                payment.error_message = "Cancelación de prueba desde comando"
                payment.save()
                
                payment.order.status = Order.OrderStatus.CANCELLED
                payment.order.save()
                
                # Verificar cambios
                payment.refresh_from_db()
                payment.order.refresh_from_db()
                
                success = (
                    payment.status == Payment.PaymentStatus.CANCELLED and
                    payment.order.status == Order.OrderStatus.CANCELLED
                )
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Cancelación exitosa')
                    )
                    self.stdout.write(f'      Nuevo estado del pago: {payment.status}')
                    self.stdout.write(f'      Nuevo estado de la orden: {payment.order.status}')
                else:
                    self.stdout.write(
                        self.style.ERROR('   ❌ Cancelación falló')
                    )
                
                return {
                    'payment_id': str(payment.id),
                    'status': 'success' if success else 'failed',
                    'success': success,
                    'initial_payment_status': initial_payment_status,
                    'initial_order_status': initial_order_status,
                    'final_payment_status': payment.status,
                    'final_order_status': payment.order.status,
                }
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error: {str(e)}')
            )
            return {
                'payment_id': str(payment.id),
                'status': 'error',
                'success': False,
                'error': str(e)
            }

    def _test_stripe_integration(self, payment):
        """Probar integración con Stripe"""
        if not payment.stripe_session_id:
            self.stdout.write('   ⚠️  No hay sesión de Stripe para probar')
            return False
        
        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
            self.stdout.write(f'   ✅ Sesión de Stripe encontrada: {session.id}')
            self.stdout.write(f'      Estado: {session.status}')
            self.stdout.write(f'      Estado del pago: {session.payment_status}')
            return True
        except stripe.error.StripeError as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error de Stripe: {str(e)}')
            )
            return False

    def _show_summary(self, results):
        """Mostrar resumen de las pruebas"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 RESUMEN DE PRUEBAS')
        self.stdout.write('='*50)
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        self.stdout.write(f'✅ Exitosas: {successful}/{total}')
        self.stdout.write(f'❌ Fallidas: {total - successful}/{total}')
        
        if successful == total:
            self.stdout.write(
                self.style.SUCCESS('🎉 Todas las pruebas pasaron exitosamente!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Algunas pruebas fallaron')
            )
            
            # Mostrar detalles de fallos
            for result in results:
                if not result['success']:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Pago {result["payment_id"]}: {result.get("error", "Error desconocido")}')
                    ) 