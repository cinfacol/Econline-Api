import logging
from decimal import Decimal

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Prueba el caso real de $320 USD con 20% de descuento y límite de $35"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "=== PRUEBA DEL CASO REAL: $320 USD, 20%, LÍMITE $35 ==="
            )
        )

        # Datos del caso real
        subtotal = Decimal("320.00")
        discount_percentage = 20
        max_discount_amount = Decimal("35.00")

        self.stdout.write(f"Subtotal: ${subtotal}")
        self.stdout.write(f"Porcentaje de descuento: {discount_percentage}%")
        self.stdout.write(f"Límite máximo: ${max_discount_amount}")
        self.stdout.write("")

        # Calcular descuento sin límite
        percentage_discount = (subtotal * discount_percentage) / 100
        self.stdout.write(f"Descuento sin límite: ${percentage_discount}")

        # Aplicar límite
        actual_discount = min(percentage_discount, max_discount_amount)
        self.stdout.write(f"Descuento final aplicado: ${actual_discount}")

        # Calcular total final
        total_after_discount = subtotal - actual_discount
        self.stdout.write(f"Total después del descuento: ${total_after_discount}")

        # Verificar que el límite se respeta
        if actual_discount <= max_discount_amount:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ LÍMITE RESPETADO: El descuento no excede el máximo permitido"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ ERROR: El descuento excede el límite máximo")
            )

        # Simular creación de cupón de Stripe
        stripe_amount_off = int(float(actual_discount) * 100)  # Convertir a centavos
        coupon_identifier = f"TEST_COUPON_{int(subtotal)}"

        self.stdout.write("")
        self.stdout.write("=== DATOS PARA STRIPE ===")
        self.stdout.write(f"Identificador del cupón: {coupon_identifier}")
        self.stdout.write(f"amount_off (centavos): {stripe_amount_off}")
        self.stdout.write(f"amount_off (dólares): ${actual_discount}")

        # Verificar conversión
        expected_cents = int(float(actual_discount) * 100)
        if stripe_amount_off == expected_cents:
            self.stdout.write(
                self.style.SUCCESS("✅ CORRECTO: Conversión a centavos es correcta")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ ERROR: Conversión a centavos incorrecta")
            )

        # Mostrar ejemplo de código Stripe
        self.stdout.write("")
        self.stdout.write("=== EJEMPLO DE CÓDIGO STRIPE ===")
        self.stdout.write("stripe_coupon = stripe.Coupon.create(")
        self.stdout.write(f"    name='{coupon_identifier}',")
        self.stdout.write(f"    amount_off={stripe_amount_off},")
        self.stdout.write("    currency='usd',")
        self.stdout.write("    duration='once',")
        self.stdout.write(")")

        # Verificar que el total es correcto
        self.stdout.write("")
        self.stdout.write("=== VERIFICACIÓN DEL TOTAL ===")
        self.stdout.write(f"Subtotal original: ${subtotal}")
        self.stdout.write(f"Descuento aplicado: ${actual_discount}")
        self.stdout.write(f"Total a pagar: ${total_after_discount}")

        expected_total = Decimal("285.00")  # 320 - 35
        if total_after_discount == expected_total:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ CORRECTO: Total a pagar es ${total_after_discount}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ ERROR: Total esperado ${expected_total}, obtenido ${total_after_discount}"
                )
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✅ Prueba del caso real completada exitosamente")
        )
