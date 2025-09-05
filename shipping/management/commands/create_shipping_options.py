from decimal import Decimal

from django.core.management.base import BaseCommand

from shipping.models import Shipping


class Command(BaseCommand):
    help = "Crea opciones de envío de ejemplo"

    def handle(self, *args, **kwargs):
        shipping_options = [
            {
                "name": "Envío Estándar",
                "time_to_delivery": "3-5 días",
                "service_type": "NACIONAL",
                "transport_type": "TERRESTRE",
                "standard_shipping_cost": Decimal("3.00"),
                "free_shipping_threshold": Decimal("15.00"),
                "is_active": True,
            },
            {
                "name": "Envío Express",
                "time_to_delivery": "1-2 días",
                "service_type": "EXPRESS",
                "transport_type": "TERRESTRE",
                "standard_shipping_cost": Decimal("5.00"),
                "free_shipping_threshold": Decimal("25.00"),
                "is_active": True,
            },
            {
                "name": "Envío Internacional",
                "time_to_delivery": "5-7 días",
                "service_type": "INTERNACIONAL",
                "transport_type": "AEREO",
                "standard_shipping_cost": Decimal("15.00"),
                "free_shipping_threshold": Decimal("50.00"),
                "is_active": True,
            },
        ]

        for option in shipping_options:
            Shipping.objects.get_or_create(name=option["name"], defaults=option)
            self.stdout.write(
                self.style.SUCCESS(f"Opción de envío creada: {option['name']}")
            )
