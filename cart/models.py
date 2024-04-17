from django.db import models
from django.conf import settings

from common.models import TimeStampedUUIDModel
from inventory.models import Inventory
from coupons.models import Coupon


User = settings.AUTH_USER_MODEL


class Cart(TimeStampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Inventory, through="CartItem")
    total_items = models.IntegerField(default=0)

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(TimeStampedUUIDModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, blank=True, null=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.inventory.product.name}"
