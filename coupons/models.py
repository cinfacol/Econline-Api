from django.db import models

# from apps.courses.models import Course
# from apps.tiers.models import Tier
# import uuid
from inventory.models import Inventory
from django.conf import settings
from common.models import TimeStampedUUIDModel

User = settings.AUTH_USER_MODEL


class Coupon(TimeStampedUUIDModel):
    types = (("inventories", "Inventories"),)
    name = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fixed_price_coupon = models.ForeignKey(
        "FixedPriceCoupon", on_delete=models.CASCADE, blank=True, null=True
    )
    percentage_coupon = models.ForeignKey(
        "PercentageCoupon", on_delete=models.CASCADE, blank=True, null=True
    )
    content_type = models.CharField(choices=types, max_length=20, default="inventories")
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
