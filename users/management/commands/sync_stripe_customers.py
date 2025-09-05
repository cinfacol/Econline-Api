import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import User


class Command(BaseCommand):
    help = "Sincroniza usuarios existentes con Stripe"

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        users = User.objects.filter(stripe_customer_id__isnull=True)

        self.stdout.write(f"Encontrados {users.count()} usuarios para sincronizar")

        with transaction.atomic():
            for user in users:
                try:
                    self.stdout.write(f"Procesando usuario: {user.email}")
                    user.get_or_create_stripe_customer()
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Usuario {user.email} sincronizado")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error con {user.email}: {str(e)}")
                    )

        self.stdout.write(self.style.SUCCESS("Sincronización completada"))
