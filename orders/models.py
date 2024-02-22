from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from inventory.models import Inventory
from common.models import TimeStampedUUIDModel

User = settings.AUTH_USER_MODEL


class Order(TimeStampedUUIDModel):

    class OrderStatus(models.TextChoices):
        PENDING = "P", _("Pending")
        COMPLETED = "C", _("Completed")
        SHIPPED = "S", _("Shipped")
        DELIVERED = "D", _("Delivered")
        CANCELLED = "X", _("Cancelled")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_name = models.CharField(max_length=255)
    shipping_time = models.CharField(max_length=255)
    shipping_price = models.DecimalField(max_digits=5, decimal_places=2)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)

    def __str__(self):
        return self.transaction_id


class OrderItem(TimeStampedUUIDModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.IntegerField()

    def __str__(self):
        return self.name
