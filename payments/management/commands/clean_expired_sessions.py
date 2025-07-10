from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Payment
from payments.tasks import handle_checkout_session_expired_task, handle_manual_payment_cancellation_task
import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpiar sesiones de checkout expiradas y marcar pagos como cancelados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la limpieza incluso si hay errores',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        self.stdout.write(
            self.style.SUCCESS('Iniciando limpieza de sesiones expiradas...')
        )
        
        # Buscar pagos pendientes con sesiones de Stripe
        pending_payments = Payment.objects.filter(
            status=Payment.PaymentStatus.PENDING,
            stripe_session_id__isnull=False
        ).select_related('order', 'user')
        
        self.stdout.write(f"Encontrados {pending_payments.count()} pagos pendientes con sesiones de Stripe")
        
        expired_count = 0
        error_count = 0
        
        for payment in pending_payments:
            try:
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Verificando sesión: {payment.stripe_session_id}")
                    continue
                
                # Verificar el estado de la sesión en Stripe
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                
                # Si la sesión ha expirado, procesar la cancelación
                if session.expires_at and session.expires_at < int(timezone.now().timestamp()):
                    self.stdout.write(
                        self.style.WARNING(f"Sesión expirada detectada: {payment.stripe_session_id}")
                    )
                    
                    # Procesar la expiración de forma asíncrona
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1
                    
                elif session.status == "expired":
                    self.stdout.write(
                        self.style.WARNING(f"Sesión marcada como expirada en Stripe: {payment.stripe_session_id}")
                    )
                    
                    # Procesar la expiración de forma asíncrona
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1
                    
            except stripe.error.InvalidRequestError:
                # La sesión no existe en Stripe, marcarla como cancelada
                self.stdout.write(
                    self.style.ERROR(f"Sesión no encontrada en Stripe: {payment.stripe_session_id}")
                )
                
                if not dry_run:
                    handle_manual_payment_cancellation_task.delay(
                        str(payment.id), 
                        str(payment.user.id), 
                        "sesión_no_encontrada_en_stripe"
                    )
                    expired_count += 1
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Error verificando sesión {payment.stripe_session_id}: {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(error_msg)
                
                if force:
                    # En modo force, intentar cancelar el pago localmente
                    if not dry_run:
                        handle_manual_payment_cancellation_task.delay(
                            str(payment.id), 
                            str(payment.user.id), 
                            f"error_verificación_stripe: {str(e)}"
                        )
                        expired_count += 1
        
        # Resumen
        self.stdout.write(
            self.style.SUCCESS(
                f"\nLimpieza completada:\n"
                f"- Sesiones expiradas procesadas: {expired_count}\n"
                f"- Errores encontrados: {error_count}\n"
                f"- Total verificadas: {pending_payments.count()}"
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("Ejecutado en modo DRY RUN - No se realizaron cambios")
            ) 