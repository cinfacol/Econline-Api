#!/usr/bin/env python3
"""
Estrategia MANUAL para verificar reembolsos - Solo cuando sea necesario
Ejecutar solo después de hacer un reembolso manualmente
"""

import os
import sys


def quick_refund_check(payment_id=None):
    """
    Verificación rápida para un payment específico o últimos reembolsos
    """

    # Configurar Django solo cuando se necesite
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()

    from payments.models import Payment, Refund

    if payment_id:
        # Verificar un payment específico
        try:
            payment = Payment.objects.get(id=payment_id)
            refunds = Refund.objects.filter(payment=payment)

            print(f"💰 PAYMENT {payment_id}:")
            print(f"   Status: {payment.get_status_display()}")
            print(f"   Refunds: {refunds.count()}")

            if payment.status == "R" and refunds.count() > 0:
                print("   ✅ Reembolso OK")
            else:
                print("   ⚠️  Requiere verificación manual")

        except Payment.DoesNotExist:
            print(f"❌ Payment {payment_id} no encontrado")
    else:
        # Verificar últimos payments sin reembolsos
        from datetime import timedelta

        from django.utils import timezone

        recent_payments = Payment.objects.filter(
            status="C",  # Completados
            updated_at__gte=timezone.now() - timedelta(hours=24),
        )

        print(f"📊 {recent_payments.count()} payments completados en últimas 24h")

        for payment in recent_payments:
            refunds = Refund.objects.filter(payment=payment)
            if refunds.count() == 0:
                print(f"   {payment.id}: Sin reembolsos (normal)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        payment_id = sys.argv[1]
        quick_refund_check(payment_id)
    else:
        print("Uso: python check_refund_manual.py [payment_id]")
        print("O sin argumentos para verificar payments recientes")
        quick_refund_check()
