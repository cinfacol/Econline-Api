#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la conectividad de webhooks de Stripe
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import stripe
import requests
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Diagnóstico de webhooks de Stripe y conectividad del tunnel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-webhook",
            action="store_true",
            help="Probar el endpoint de webhook directamente",
        )
        parser.add_argument(
            "--check-stripe",
            action="store_true",
            help="Verificar configuración en Stripe Dashboard",
        )
        parser.add_argument(
            "--list-events",
            action="store_true",
            help="Listar eventos recientes de Stripe",
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        self.stdout.write(self.style.SUCCESS("🔍 Iniciando diagnóstico de webhooks..."))

        if options.get("test_webhook"):
            self.test_webhook_endpoint()

        if options.get("check_stripe"):
            self.check_stripe_configuration()

        if options.get("list_events"):
            self.list_recent_stripe_events()

        # Diagnóstico general
        self.general_webhook_diagnostic()

    def test_webhook_endpoint(self):
        """Probar el endpoint de webhook directamente"""
        self.stdout.write("🔧 Probando endpoint de webhook...")

        # URLs a probar
        urls_to_test = [
            f"{settings.FRONTEND_URL.replace('3000', '9090')}/api/payments/stripe-webhook/",
            "https://api.virtualeline.com/api/payments/stripe-webhook/",
            "http://localhost:9090/api/payments/stripe-webhook/",
        ]

        for url in urls_to_test:
            self.stdout.write(f"  📡 Probando: {url}")
            try:
                # Test simple GET (debería devolver 405 Method Not Allowed)
                response = requests.get(url, timeout=10)
                if response.status_code == 405:
                    self.stdout.write(
                        self.style.SUCCESS(f"    ✅ Endpoint accesible (405 esperado)")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    ⚠️  Status inesperado: {response.status_code}"
                        )
                    )
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"    ❌ Error: {str(e)}"))

    def check_stripe_configuration(self):
        """Verificar configuración de webhooks en Stripe"""
        self.stdout.write("🔧 Verificando configuración en Stripe...")

        try:
            webhook_endpoints = stripe.WebhookEndpoint.list()

            self.stdout.write(
                f"📋 Encontrados {len(webhook_endpoints.data)} webhook endpoints:"
            )

            for endpoint in webhook_endpoints.data:
                self.stdout.write(f"  🔗 URL: {endpoint.url}")
                self.stdout.write(f"    📊 Status: {endpoint.status}")
                self.stdout.write(
                    f"    🎯 Eventos: {len(endpoint.enabled_events)} configurados"
                )

                # Verificar si es nuestro endpoint
                if "virtualeline.com" in endpoint.url or "econline" in endpoint.url:
                    self.stdout.write(
                        self.style.SUCCESS(f"    ✅ Este parece ser nuestro endpoint")
                    )

                    # Verificar eventos críticos
                    critical_events = [
                        "checkout.session.completed",
                        "payment_intent.succeeded",
                        "charge.succeeded",
                    ]

                    for event in critical_events:
                        if event in endpoint.enabled_events:
                            self.stdout.write(f"    ✅ {event} configurado")
                        else:
                            self.stdout.write(
                                self.style.ERROR(f"    ❌ {event} NO configurado")
                            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error consultando Stripe: {str(e)}")
            )

    def list_recent_stripe_events(self):
        """Listar eventos recientes de Stripe"""
        self.stdout.write("📋 Listando eventos recientes de Stripe...")

        try:
            # Eventos de las últimas 24 horas
            events = stripe.Event.list(
                limit=20,
                created={"gte": int((datetime.now() - timedelta(days=1)).timestamp())},
            )

            webhook_events = [
                "checkout.session.completed",
                "payment_intent.succeeded",
                "charge.succeeded",
                "payment_intent.payment_failed",
            ]

            relevant_events = [e for e in events.data if e.type in webhook_events]

            self.stdout.write(
                f"🎯 Eventos relevantes en las últimas 24h: {len(relevant_events)}"
            )

            for event in relevant_events[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(f"  📅 {datetime.fromtimestamp(event.created)}")
                self.stdout.write(f"    🎭 Tipo: {event.type}")
                self.stdout.write(f"    🆔 ID: {event.id}")

                # Intentar obtener payment_id de metadata
                try:
                    payment_id = event.data.object.get("metadata", {}).get("payment_id")
                    if payment_id:
                        self.stdout.write(f"    💳 Payment ID: {payment_id}")
                except:
                    pass

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error listando eventos: {str(e)}"))

    def general_webhook_diagnostic(self):
        """Diagnóstico general de webhooks"""
        self.stdout.write("🔍 Diagnóstico general...")

        # Verificar configuración Django
        self.stdout.write("⚙️  Configuración Django:")

        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
        if webhook_secret:
            self.stdout.write("  ✅ STRIPE_WEBHOOK_SECRET configurado")
        else:
            self.stdout.write(
                self.style.ERROR("  ❌ STRIPE_WEBHOOK_SECRET NO configurado")
            )

        # Verificar Celery
        try:
            from celery import current_app

            i = current_app.control.inspect()
            if i.ping():
                self.stdout.write("  ✅ Celery funcionando")
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  Celery no responde"))
        except Exception:
            self.stdout.write(self.style.ERROR("  ❌ Error verificando Celery"))

        # Verificar base de datos de pagos recientes
        try:
            from payments.models import Payment

            recent_payments = Payment.objects.filter(
                created_at__gte=datetime.now() - timedelta(hours=24)
            ).count()

            pending_payments = Payment.objects.filter(
                status="P", created_at__gte=datetime.now() - timedelta(hours=24)
            ).count()

            self.stdout.write(
                f"💳 Pagos últimas 24h: {recent_payments} total, {pending_payments} pendientes"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error consultando BD: {str(e)}"))
