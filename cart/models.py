import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.manager import Manager

from common.models import TimeStampedUUIDModel
from inventory.models import Inventory
from coupons.models import Coupon

from decimal import Decimal

logger = logging.getLogger(__name__)

User = get_user_model()


class Cart(TimeStampedUUIDModel):
    objects: Manager = models.Manager()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(
        Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="carts"
    )
    total_items = models.IntegerField(default=0)

    def get_subtotal(self):
        try:
            subtotal = Decimal("0")
            for item in self.items.all():
                price = Decimal(str(item.inventory.store_price))
                quantity = Decimal(str(item.quantity))
                subtotal += price * quantity
            return subtotal
        except (TypeError, ValueError) as e:
            logger.error(f"Error calculating cart subtotal: {str(e)}")
            return Decimal("0")

    def get_total_items(self):
        return self.items.count()

    def get_discount(self):
        try:
            discount = Decimal("0")
            if not self.coupon:
                return Decimal("0")
            
            subtotal = self.get_subtotal()
            
            # Verificar si el cupón es válido para el subtotal actual
            if self.coupon.min_purchase_amount and subtotal < self.coupon.min_purchase_amount:
                return Decimal("0")
            
            # Calcular descuento basado en el tipo de cupón
            if self.coupon.percentage_coupon:
                # Cupón de porcentaje
                discount = (subtotal * self.coupon.percentage_coupon.discount_percentage) / 100
                # Aplicar máximo descuento si está configurado
                if self.coupon.max_discount_amount:
                    discount = min(discount, self.coupon.max_discount_amount)
            elif self.coupon.fixed_price_coupon:
                # Cupón de monto fijo
                discount = self.coupon.fixed_price_coupon.discount_price
            
            return discount
        except (TypeError, ValueError) as e:
            logger.error(f"Error calculating cart discount: {str(e)}")
            return Decimal("0")

    def get_total(self):
        return self.get_subtotal() - self.get_discount()

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(TimeStampedUUIDModel):
    cart = models.ForeignKey("Cart", related_name="items", on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank=True, null=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        ordering = ["-created_at"]

    def get_total(self):
        return self.quantity * self.inventory.store_price

    def __str__(self):
        return f"{self.quantity} x {self.inventory.product.name}"


class DeliveryCost(TimeStampedUUIDModel):
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=7,
        choices=(("Active", "active"), ("Passive", "passive")),
        default="passive",
        null=False,
    )
    cost_per_delivery = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    cost_per_product = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    fixed_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    def __str__(self):
        return f"{self.name} - {self.status} - {self.cost_per_delivery} - {self.cost_per_product} - {self.fixed_cost}"
