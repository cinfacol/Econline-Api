from django.db import models
from common.models import TimeStampedUUIDModel
from decimal import Decimal


class Shipping(TimeStampedUUIDModel):
    class Meta:
        verbose_name = "Shipping"
        verbose_name_plural = "Shipping"

    # Campos básicos
    name = models.CharField(max_length=255, unique=True)
    time_to_delivery = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Campos para Servientrega
    service_type = models.CharField(
        max_length=50,
        choices=[
            ('NACIONAL', 'Nacional'),
            ('INTERNACIONAL', 'Internacional'),
            ('EXPRESS', 'Express'),
            ('ESPECIAL', 'Especial')
        ],
        default='NACIONAL'
    )
    transport_type = models.CharField(
        max_length=50,
        choices=[
            ('TERRESTRE', 'Terrestre'),
            ('AEREO', 'Aéreo')
        ],
        default='TERRESTRE'
    )
    is_active = models.BooleanField(default=True)
    
    # Campos para cálculo de costos
    free_shipping_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('15.00'),
        help_text="Monto mínimo para envío gratuito"
    )
    standard_shipping_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('3.00'),
        help_text="Costo estándar de envío"
    )

    def __str__(self):
        return self.name

    def calculate_shipping_cost(self, order_total: Decimal) -> Decimal:
        """
        Calcula el costo de envío basado en el total de la orden
        """
        if order_total >= self.free_shipping_threshold:
            return Decimal('0.00')
        return self.standard_shipping_cost

    def get_estimated_delivery_days(self) -> str:
        """
        Retorna los días estimados de entrega basado en el tipo de servicio
        """
        if self.service_type == 'EXPRESS':
            return '1-2 días'
        elif self.service_type == 'NACIONAL':
            return '3-5 días'
        elif self.service_type == 'INTERNACIONAL':
            return '5-7 días'
        return '7-10 días'
