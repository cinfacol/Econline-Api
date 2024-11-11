from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from .contries import Countries

from inventory.models import Inventory
from common.models import TimeStampedUUIDModel
from profiles.models import Address

User = settings.AUTH_USER_MODEL


class Order(TimeStampedUUIDModel):

    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        COMPLETED = "COMPLETED", _("Completed")
        SHIPPED = "SHIPPED", _("Shipped")
        DELIVERED = "DELIVERED", _("Delivered")
        CANCELLED = "CANCELLED", _("Cancelled")

    status = models.CharField(
        verbose_name=_("Status"),
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    full_name = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state_province_region = models.CharField(max_length=255)
    postal_zip_code = models.CharField(max_length=20)
    country_region = models.CharField(
        max_length=255, choices=Countries.choices, default=Countries.Colombia
    )
    telephone_number = models.CharField(max_length=255)
    """ shipping_address = models.ForeignKey(
        Address,
        related_name="shipping_orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    billing_address = models.ForeignKey(
        Address,
        related_name="billing_orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    ) """
    shipping_name = models.CharField(max_length=255)
    shipping_time = models.CharField(max_length=255)
    shipping_price = models.DecimalField(max_digits=5, decimal_places=2)
    # is_delivered = models.BooleanField(default=False)
    date_issued = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.transaction_id


class OrderItem(TimeStampedUUIDModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.IntegerField()

    def __str__(self):
        return self.order.transaction_id

    @cached_property
    def cost(self):
        """
        Total cost of the ordered item
        """
        return round(self.count * self.inventory.store_price, 2)
