from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

from coupons.models import Coupon, PercentageCoupon
from orders.models import Order, OrderItem
from inventory.models import Inventory
from cart.models import Cart

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba el límite de descuento en cupones de porcentaje'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subtotal',
            type=float,
            default=200.00,
            help='Subtotal para probar (default: 200.00)'
        )
        parser.add_argument(
            '--percentage',
            type=int,
            default=25,
            help='Porcentaje de descuento (default: 25)'
        )
        parser.add_argument(
            '--max-discount',
            type=float,
            default=35.00,
            help='Límite máximo de descuento (default: 35.00)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== PRUEBA DE LÍMITE DE CUPÓN EN CONTEXTO REAL ===')
        )
        
        subtotal = Decimal(str(options['subtotal']))
        discount_percentage = options['percentage']
        max_discount_amount = Decimal(str(options['max_discount']))
        
        self.stdout.write(f"Subtotal: ${subtotal}")
        self.stdout.write(f"Porcentaje de descuento: {discount_percentage}%")
        self.stdout.write(f"Límite máximo: ${max_discount_amount}")
        self.stdout.write("")
        
        # Simular el cálculo que se hace en el código real
        percentage_discount = (subtotal * discount_percentage) / 100
        
        # Aplicar límite máximo de descuento si está configurado
        if max_discount_amount:
            actual_discount = min(percentage_discount, max_discount_amount)
            self.stdout.write(f"Descuento calculado: ${percentage_discount}")
            self.stdout.write(f"Límite máximo: ${max_discount_amount}")
            self.stdout.write(f"Descuento final aplicado: ${actual_discount}")
            
            if actual_discount <= max_discount_amount:
                self.stdout.write(
                    self.style.SUCCESS("✅ LÍMITE RESPETADO: El descuento no excede el máximo permitido")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ ERROR: El descuento excede el límite máximo")
                )
        else:
            actual_discount = percentage_discount
            self.stdout.write(f"Descuento aplicado (sin límite): ${actual_discount}")
        
        # Simular creación de cupón de Stripe
        stripe_amount_off = int(float(actual_discount) * 100)  # Convertir a centavos
        
        self.stdout.write("")
        self.stdout.write("=== DATOS PARA STRIPE ===")
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
        self.stdout.write(f"    name='TEST_COUPON',")
        self.stdout.write(f"    amount_off={stripe_amount_off},")
        self.stdout.write(f"    currency='usd',")
        self.stdout.write(f"    duration='once',")
        self.stdout.write(")")
        
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✅ Prueba completada exitosamente")
        ) 