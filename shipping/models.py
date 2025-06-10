import logging
from django.db import models
from common.models import TimeStampedUUIDModel
from decimal import Decimal
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Shipping(TimeStampedUUIDModel):
    class Meta:
        verbose_name = "Shipping"
        verbose_name_plural = "Shipping"

    # Campos básicos
    name = models.CharField(max_length=255, unique=True)
    time_to_delivery = models.CharField(max_length=255)

    # Campos para Servientrega
    service_type = models.CharField(
        max_length=50,
        choices=[
            ("NACIONAL", "Nacional"),
            ("INTERNACIONAL", "Internacional"),
            ("EXPRESS", "Express"),
            ("ESPECIAL", "Especial"),
        ],
        default="NACIONAL",
    )
    transport_type = models.CharField(
        max_length=50,
        choices=[("TERRESTRE", "Terrestre"), ("AEREO", "Aéreo")],
        default="TERRESTRE",
    )
    is_active = models.BooleanField(default=True)

    # Campos para cálculo de costos
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("15.00"),
        help_text="Monto mínimo para envío gratuito",
    )
    standard_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("3.00"),
        help_text="Costo estándar de envío",
    )

    def __str__(self):
        return self.name

    def calculate_shipping_cost(self, subtotal):
        try:
            subtotal = Decimal(str(subtotal))
            standard_cost = Decimal(str(self.standard_shipping_cost))
            threshold = Decimal(str(self.free_shipping_threshold))

            if subtotal >= threshold:
                return Decimal("0")
            return standard_cost
        except (TypeError, ValueError) as e:
            logger.error(f"Error calculating shipping cost: {str(e)}")
            raise ValidationError(_("Error al calcular el costo de envío."))

    def get_estimated_delivery_days(self) -> str:
        """
        Retorna los días estimados de entrega basado en el tipo de servicio
        """
        if self.service_type == "EXPRESS":
            return "1-2 días"
        elif self.service_type == "NACIONAL":
            return "3-5 días"
        elif self.service_type == "INTERNACIONAL":
            return "5-7 días"
        return "7-10 días"
