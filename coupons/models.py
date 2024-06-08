from django.db import models

from inventory.models import Inventory
from categories.models import Category
from django.conf import settings
from common.models import TimeStampedUUIDModel

User = settings.AUTH_USER_MODEL


class Coupon(TimeStampedUUIDModel):
    name = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fixed_price_coupon = models.ForeignKey(
        "FixedPriceCoupon", on_delete=models.CASCADE, blank=True, null=True
    )
    percentage_coupon = models.ForeignKey(
        "PercentageCoupon", on_delete=models.CASCADE, blank=True, null=True
    )
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.name


class FixedPriceCoupon(TimeStampedUUIDModel):
    discount_price = models.DecimalField(max_digits=5, decimal_places=2)
    uses = models.IntegerField()


class PercentageCoupon(TimeStampedUUIDModel):
    discount_percentage = models.IntegerField()
    uses = models.IntegerField()


class Campaign(TimeStampedUUIDModel):
    discount_type = models.CharField(
        max_length=6,
        choices=(("Amount", "amount"), ("Rate", "rate")),
        default="rate",
        null=False,
    )
    discount_rate = models.IntegerField(null=True, blank=True)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    min_purchased_items = models.IntegerField(null=False)
    apply_to = models.CharField(
        max_length=8,
        choices=(("Product", "product"), ("Category", "category")),
        default="product",
        null=False,
    )
    target_product = models.ForeignKey(
        Inventory, on_delete=models.SET_NULL, null=True, blank=True
    )
    target_category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return "{} - {} - {} - {} - {} - {} - {}".format(
            self.discount_type,
            self.discount_rate,
            self.discount_amount,
            self.min_purchased_items,
            self.apply_to,
            self.target_product,
            self.target_category,
        )
