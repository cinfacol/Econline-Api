#!/usr/bin/env python3
"""
Monitor LIGERO para webhooks faltantes - Solo para reembolsos críticos
Consumo mínimo de recursos, ejecución bajo demanda
"""

import os
from datetime import datetime, timedelta

import django
import stripe
from django.conf import settings

from payments.models import Payment, Refund

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def check_recent_refunds_only():
    """
    Verificar SOLO reembolsos de las últimas 2 horas (más eficiente)
    """
    print("🔍 VERIFICACIÓN RÁPIDA - Últimas 2 horas...")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Solo últimas 2 horas para minimizar consultas
    two_hours_ago = int((datetime.now() - timedelta(hours=2)).timestamp())

    try:
        # Limitar a 10 eventos máximo
        events = stripe.Event.list(
            type="charge.refunded", created={"gte": two_hours_ago}, limit=10
        )

        missing_count = 0

        for event in events.data:
            charge_data = event.data.object
            metadata = charge_data.get("metadata", {})
            payment_id = metadata.get("payment_id")

            if payment_id:
                try:
                    payment = Payment.objects.get(id=payment_id)
                    if not Refund.objects.filter(payment=payment).exists():
                        print(
                            f"⚠️  REEMBOLSO FALTANTE: {payment_id} - ${charge_data.amount_refunded / 100}"
                        )
                        missing_count += 1
                except Payment.DoesNotExist:
                    pass

        if missing_count == 0:
            print("✅ Todos los reembolsos están sincronizados")
        else:
            print(f"❌ {missing_count} reembolsos requieren atención manual")

        return missing_count

    except Exception as e:
        print(f"❌ Error: {e}")
        return -1


if __name__ == "__main__":
    missing = check_recent_refunds_only()
    exit(missing if missing > 0 else 0)  # Exit code indica si hay problemas
