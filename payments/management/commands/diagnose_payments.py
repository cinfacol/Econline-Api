#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de pagos y sincronización con Stripe
"""

import logging

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order
from payments.models import Payment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Diagnóstico de pagos y sincronización con Stripe"

    def add_arguments(self, parser):
        parser.add_argument(
            "--payment-id", type=str, help="ID específico de pago para diagnosticar"
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Intentar arreglar discrepancias encontradas",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Días hacia atrás para revisar pagos (default: 7)",
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payment_id = options.get("payment_id")
        fix_issues = options.get("fix")
        days_back = options.get("days")

        self.stdout.write(self.style.SUCCESS("🔍 Iniciando diagnóstico de pagos..."))

        if payment_id:
            self.diagnose_single_payment(payment_id, fix_issues)
        else:
            self.diagnose_recent_payments(days_back, fix_issues)

    def diagnose_single_payment(self, payment_id, fix_issues):
        try:
            payment = Payment.objects.select_related("order").get(id=payment_id)
            self.stdout.write(f"📋 Analizando pago: {payment.id}")
            self.check_payment_status(payment, fix_issues)
        except Payment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Pago {payment_id} no encontrado"))

    def diagnose_recent_payments(self, days_back, fix_issues):
        cutoff_date = timezone.now() - timezone.timedelta(days=days_back)
        payments = (
            Payment.objects.select_related("order")
            .filter(created_at__gte=cutoff_date)
            .order_by("-created_at")
        )

        self.stdout.write(
            f"📋 Analizando {payments.count()} pagos de los últimos {days_back} días"
        )

        pending_count = 0
        completed_count = 0
        discrepancies = 0

        for payment in payments:
            status = self.check_payment_status(payment, fix_issues)
            if status == "pending":
                pending_count += 1
            elif status == "completed":
                completed_count += 1
            elif status == "discrepancy":
                discrepancies += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"📊 Resumen: {completed_count} completados, "
                f"{pending_count} pendientes, {discrepancies} discrepancias"
            )
        )

    def check_payment_status(self, payment, fix_issues):
        self.stdout.write(
            f"  💳 Pago {payment.id[:8]}... Estado local: {payment.status}"
        )

        if not payment.stripe_session_id:
            self.stdout.write("    ⚠️  Sin session_id de Stripe")
            return "no_stripe"

        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
            stripe_status = session.payment_status

            self.stdout.write(f"    🔗 Estado en Stripe: {stripe_status}")

            # Verificar discrepancias
            if (
                stripe_status == "paid"
                and payment.status != Payment.PaymentStatus.COMPLETED
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"    ⚠️  DISCREPANCIA: Stripe dice 'paid' pero local es '{payment.status}'"
                    )
                )

                if fix_issues:
                    self.fix_payment_discrepancy(payment, session)
                    return "fixed"
                else:
                    self.stdout.write("    💡 Usa --fix para corregir automáticamente")
                    return "discrepancy"

            elif (
                stripe_status == "unpaid"
                and payment.status == Payment.PaymentStatus.COMPLETED
            ):
                self.stdout.write(
                    self.style.ERROR(
                        "    ❌ PROBLEMA: Local dice 'completed' pero Stripe dice 'unpaid'"
                    )
                )
                return "discrepancy"

            else:
                self.stdout.write("    ✅ Estados sincronizados")
                return (
                    "completed"
                    if payment.status == Payment.PaymentStatus.COMPLETED
                    else "pending"
                )

        except stripe.error.StripeError as e:
            self.stdout.write(
                self.style.ERROR(f"    ❌ Error consultando Stripe: {str(e)}")
            )
            return "stripe_error"

    def fix_payment_discrepancy(self, payment, session):
        try:
            self.stdout.write("    🔧 Corrigiendo discrepancia...")

            payment.status = Payment.PaymentStatus.COMPLETED
            payment.paid_at = timezone.now()
            payment.save()

            # Actualizar orden
            payment.order.status = Order.OrderStatus.COMPLETED
            payment.order.save()

            self.stdout.write(
                self.style.SUCCESS("    ✅ Pago y orden marcados como completados")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    ❌ Error corrigiendo: {str(e)}"))
