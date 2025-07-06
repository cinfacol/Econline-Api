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
    total_items = models.IntegerField(default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    def get_total(self):
        try:
            total = Decimal("0")
            for item in self.items.all():
                price = Decimal(str(item.inventory.store_price))
                quantity = Decimal(str(item.quantity))
                total += price * quantity

            # Apply coupon discount if a coupon is associated and valid
            if (
                self.coupon and self.coupon.is_active
            ):  # Basic check, more detailed validation needed in views
                # Assuming coupon validation and discount calculation logic is available/imported
                # For now, a simplified example:
                # discount_amount = calculate_discount(self.coupon, total)
                # total -= discount_amount
                pass  # Placeholder for actual coupon application logic

            return total
        except (TypeError, ValueError) as e:
            logger.error(f"Error calculating cart total: {str(e)}")
            return Decimal("0")

    def get_total_items(self):
        return self.items.count()

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(TimeStampedUUIDModel):
    cart = models.ForeignKey("Cart", related_name="items", on_delete=models.CASCADE)
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
