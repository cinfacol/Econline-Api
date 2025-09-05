"""
Comando de administración para procesar webhooks pendientes de Stripe
"""

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand

from payments.models import Payment
from payments.webhooks import WebhookHandler


class Command(BaseCommand):
    help = "Procesa webhooks pendientes de Stripe para actualizar el estado de pagos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Número de horas hacia atrás para buscar eventos de Stripe (por defecto: 24)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Límite de eventos a procesar (por defecto: 50)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se haría sin hacer cambios reales",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        self.stdout.write(
            f"🔍 Buscando eventos de Stripe de las últimas {hours} horas..."
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🧪 Modo DRY RUN - No se harán cambios reales")
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        WebhookHandler()

        # Calcular timestamp para buscar eventos
        from datetime import datetime, timedelta

        since_time = datetime.now() - timedelta(hours=hours)
        since_timestamp = int(since_time.timestamp())

        try:
            # Obtener eventos de Stripe
            events = stripe.Event.list(
                limit=limit,
                created={"gte": since_timestamp},
                type="checkout.session.completed",
            )

            self.stdout.write(
                f"📋 Encontrados {len(events.data)} eventos checkout.session.completed"
            )

            processed_count = 0
            updated_count = 0

            for event in events.data:
                try:
                    # Verificar si tenemos metadata con order_id
                    checkout_session = event.data.object
                    metadata = checkout_session.get("metadata", {})
                    order_id = metadata.get("order_id")
                    payment_id = metadata.get("payment_id")

                    if not order_id or not payment_id:
                        self.stdout.write(
                            f"⚠️  Evento {event.id} sin metadata requerida (order_id: {order_id}, payment_id: {payment_id})"
                        )
                        continue

                    # Buscar el pago en nuestra base de datos
                    try:
                        payment = Payment.objects.get(id=payment_id)

                        if payment.status == "COMPLETED":
                            self.stdout.write(
                                f"✅ Pago {payment_id} ya está completado"
                            )
                            continue

                        self.stdout.write(
                            f"🔄 Procesando evento {event.id} para pago {payment_id} (orden: {order_id})"
                        )

                        if not dry_run:
                            # Procesar el webhook directamente usando la tarea
                            from payments.tasks import (
                                handle_checkout_session_completed_task,
                            )

                            handle_checkout_session_completed_task(checkout_session)
                            updated_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Pago {payment_id} actualizado correctamente"
                                )
                            )
                        else:
                            self.stdout.write(
                                f"🧪 DRY RUN: Se actualizaría el pago {payment_id}"
                            )

                        processed_count += 1

                    except Payment.DoesNotExist:
                        self.stdout.write(
                            f"⚠️  Pago {payment_id} no encontrado en la base de datos"
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error procesando evento {event.id}: {e}")
                    )

            # Resumen
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("📊 Resumen:")
            self.stdout.write(f"   • Eventos procesados: {processed_count}")
            if not dry_run:
                self.stdout.write(f"   • Pagos actualizados: {updated_count}")
            else:
                self.stdout.write(f"   • Pagos que se actualizarían: {processed_count}")

            # Mostrar pagos pendientes actuales
            pending_payments = Payment.objects.filter(status="PENDING").count()
            self.stdout.write(f"   • Pagos pendientes restantes: {pending_payments}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error obteniendo eventos de Stripe: {e}")
            )
