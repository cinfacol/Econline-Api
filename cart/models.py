from django.db import models
from django.contrib.auth import get_user_model

from common.models import TimeStampedUUIDModel
from inventory.models import Inventory
from coupons.models import Coupon


User = get_user_model()


class Cart(TimeStampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='carts'
    )
    total_items = models.IntegerField(default=0)

    def get_subtotal(self):
        return sum(item.get_total() for item in self.items.all())

    def get_total_items(self):
        return self.items.count()

    def get_discount(self):
        if not self.coupon:
            return 0
        return (self.get_subtotal() * self.coupon.discount) / 100

    def get_total(self):
        return self.get_subtotal() - self.get_discount()

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(TimeStampedUUIDModel):
    cart = models.ForeignKey('Cart', related_name='items', on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank=True, null=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        ordering = ['-created_at']

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
        return "{} - {} - {} - {} - {}".format(
            self.name,
            self.status,
            self.cost_per_delivery,
            self.cost_per_product,
            self.fixed_cost,
        )
