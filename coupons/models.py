import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from categories.models import Category
from common.models import TimeStampedUUIDModel
from inventory.models import Inventory
from orders.models import Order

from .fields import UpperCaseCharField

User = settings.AUTH_USER_MODEL


class PercentageCoupon(TimeStampedUUIDModel):
    discount_percentage = models.IntegerField()
    uses = models.IntegerField()


class FixedPriceCoupon(TimeStampedUUIDModel):
    discount_price = models.DecimalField(max_digits=5, decimal_places=2)
    uses = models.IntegerField()


def get_default_end_date():
    return timezone.now() + timezone.timedelta(days=30)


class Coupon(TimeStampedUUIDModel):
    name = UpperCaseCharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    fixed_price_coupon = models.ForeignKey(
        FixedPriceCoupon, on_delete=models.CASCADE, blank=True, null=True
    )
    percentage_coupon = models.ForeignKey(
        PercentageCoupon, on_delete=models.CASCADE, blank=True, null=True
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=get_default_end_date)
    min_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    max_uses = models.IntegerField(default=1)
    max_uses_per_user = models.IntegerField(default=1)
    APPLY_TO_CHOICES = [
        ("ALL", "All Products"),
        ("CATEGORY", "Specific Categories"),
        ("PRODUCT", "Specific Products"),
    ]
    apply_to = models.CharField(max_length=10, choices=APPLY_TO_CHOICES, default="ALL")

    # Relaciones para productos y categorías específicas
    categories = models.ManyToManyField("categories.Category", blank=True)
    products = models.ManyToManyField("inventory.Inventory", blank=True)
    is_active = models.BooleanField(default=True)
    can_combine = models.BooleanField(default=False)
    first_purchase_only = models.BooleanField(default=False)

    # Seguimiento
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_coupons"
    )
    used_by = models.ManyToManyField(
        User, through="CouponUsage", related_name="used_coupons"
    )

    @classmethod
    def generate_unique_code(cls, prefix="CUP"):
        while True:
            # Genera un código como CUP-XXXX-XXXX
            code = f"{prefix}-{str(uuid.uuid4())[:4].upper()}-{str(uuid.uuid4())[:4].upper()}"
            if not cls.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class CouponUsage(TimeStampedUUIDModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)


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
        return f"{self.discount_type} - {self.discount_rate} - {self.discount_amount} - {self.min_purchased_items} - {self.apply_to} - {self.target_product} - {self.target_category}"
