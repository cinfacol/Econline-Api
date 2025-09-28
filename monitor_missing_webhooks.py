#!/usr/bin/env python3
"""
Monitor para verificar webhooks faltantes y procesarlos automáticamente
"""

import os
from datetime import datetime, timedelta

import django
import stripe
from django.conf import settings

from payments.models import Payment, Refund
from payments.tasks import handle_refund_succeeded_task

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Django imports después de setup


def check_missing_refunds():
    """
    Verificar pagos que deberían tener reembolsos pero no los tienen
    """
    print("🔍 VERIFICANDO WEBHOOKS FALTANTES...")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Buscar eventos de reembolso de las últimas 24 horas
    yesterday = int((datetime.now() - timedelta(days=1)).timestamp())

    try:
        events = stripe.Event.list(
            type="charge.refunded", created={"gte": yesterday}, limit=50
        )

        print(f"📊 Encontrados {len(events.data)} eventos charge.refunded en Stripe")

        for event in events.data:
            charge_data = event.data.object
            charge_id = charge_data.id

            # Buscar el payment_id en los metadatos
            metadata = charge_data.get("metadata", {})
            payment_id = metadata.get("payment_id")

            if not payment_id:
                print(f"⚠️  Evento {event.id} sin payment_id en metadata")
                continue

            try:
                payment = Payment.objects.get(id=payment_id)

                # Verificar si ya tiene reembolso
                existing_refunds = Refund.objects.filter(payment=payment)

                if existing_refunds.exists():
                    print(f"✅ Payment {payment_id} ya tiene reembolso")
                    continue

                if payment.status != "R":  # No está reembolsado
                    print(f"🔄 Procesando reembolso faltante para payment {payment_id}")
                    print(f"   Charge: {charge_id}")
                    print(f"   Amount: ${charge_data.amount_refunded / 100}")

                    # Procesar el reembolso faltante
                    handle_refund_succeeded_task(charge_data)
                    print("   ✅ Procesado exitosamente")
                else:
                    print(f"✅ Payment {payment_id} ya está marcado como reembolsado")

            except Payment.DoesNotExist:
                print(f"❌ Payment {payment_id} no encontrado en la base de datos")
            except Exception as e:
                print(f"❌ Error procesando {payment_id}: {e}")

    except Exception as e:
        print(f"❌ Error obteniendo eventos de Stripe: {e}")


def test_webhook_connectivity():
    """
    Probar conectividad del webhook
    """
    print("\n🌐 PROBANDO CONECTIVIDAD DEL WEBHOOK...")

    import requests

    webhook_url = "https://api.virtualeline.com/stripe_webhook/"

    try:
        response = requests.get(webhook_url, timeout=10)
        if response.status_code in [400, 405]:  # Esperados para GET
            print("✅ Webhook accesible externamente")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")


if __name__ == "__main__":
    print("🚀 MONITOR DE WEBHOOKS FALTANTES")
    print("=" * 50)

    check_missing_refunds()
    test_webhook_connectivity()

    print("\n✅ Verificación completada")
