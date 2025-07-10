from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from payments.models import Payment
from orders.models import Order
from django.db import transaction
import time

User = get_user_model()

class Command(BaseCommand):
    help = 'Verificar el estado de los pagos en tiempo real'

    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            type=str,
            help='ID específico del pago a monitorear',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email del usuario para buscar pagos',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Intervalo en segundos entre verificaciones (default: 5)',
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duración total del monitoreo en segundos (default: 60)',
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Monitorear continuamente hasta que se presione Ctrl+C',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando monitoreo de pagos')
        )
        
        # Buscar pagos para monitorear
        payments = self._find_payments(options)
        
        if not payments:
            self.stdout.write(
                self.style.WARNING('⚠️  No se encontraron pagos para monitorear')
            )
            return
        
        self.stdout.write(f'✅ Monitoreando {len(payments)} pagos')
        
        # Mostrar información inicial
        self._show_payment_status(payments, "Estado inicial")
        
        if options['watch']:
            # Modo continuo
            self._monitor_continuously(payments, options['interval'])
        else:
            # Modo con duración limitada
            self._monitor_with_duration(payments, options['interval'], options['duration'])

    def _find_payments(self, options):
        """Encontrar pagos para monitorear"""
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

    def _show_payment_status(self, payments, title):
        """Mostrar el estado de los pagos"""
        self.stdout.write(f'\n📊 {title}')
        self.stdout.write('=' * 80)
        
        for payment in payments:
            # Refrescar desde la base de datos
            payment.refresh_from_db()
            payment.order.refresh_from_db()
            
            self.stdout.write(
                f'💰 Pago: {payment.id} | '
                f'Orden: {payment.order.id} | '
                f'Usuario: {payment.order.user.email}'
            )
            self.stdout.write(
                f'   Estado Pago: {payment.status} ({payment.get_status_display()}) | '
                f'Estado Orden: {payment.order.status} ({payment.order.get_status_display()})'
            )
            self.stdout.write(
                f'   Monto: {payment.amount} {payment.currency} | '
                f'Creado: {payment.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
            )
            if payment.stripe_session_id:
                self.stdout.write(f'   Stripe Session: {payment.stripe_session_id}')
            self.stdout.write('')

    def _monitor_continuously(self, payments, interval):
        """Monitorear continuamente hasta Ctrl+C"""
        try:
            iteration = 1
            while True:
                self._show_payment_status(payments, f"Iteración {iteration}")
                self.stdout.write(f'⏳ Esperando {interval} segundos... (Ctrl+C para salir)')
                time.sleep(interval)
                iteration += 1
        except KeyboardInterrupt:
            self.stdout.write('\n🛑 Monitoreo detenido por el usuario')

    def _monitor_with_duration(self, payments, interval, duration):
        """Monitorear por una duración específica"""
        iterations = duration // interval
        self.stdout.write(f'⏱️  Monitoreando por {duration} segundos ({iterations} iteraciones)')
        
        for i in range(iterations):
            self._show_payment_status(payments, f"Iteración {i+1}/{iterations}")
            
            if i < iterations - 1:  # No esperar en la última iteración
                self.stdout.write(f'⏳ Esperando {interval} segundos...')
                time.sleep(interval)
        
        self.stdout.write('\n✅ Monitoreo completado')

    def _check_for_changes(self, payments, previous_states):
        """Verificar si hubo cambios en los pagos"""
        changes = []
        
        for payment in payments:
            payment.refresh_from_db()
            payment.order.refresh_from_db()
            
            payment_key = str(payment.id)
            if payment_key in previous_states:
                prev_state = previous_states[payment_key]
                current_state = {
                    'payment_status': payment.status,
                    'order_status': payment.order.status,
                }
                
                if prev_state != current_state:
                    changes.append({
                        'payment_id': payment.id,
                        'previous': prev_state,
                        'current': current_state,
                    })
        
        return changes 