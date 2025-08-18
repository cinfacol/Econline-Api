from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from .contries import Countries

from inventory.models import Inventory
from common.models import TimeStampedUUIDModel
from users.models import User, Address
from shipping.models import Shipping


class Order(TimeStampedUUIDModel):

    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        COMPLETED = "COMPLETED", _("Completed")
        SHIPPED = "SHIPPED", _("Shipped")
        DELIVERED = "DELIVERED", _("Delivered")
        CANCELLED = "CANCELLED", _("Cancelled")

    transaction_id = models.CharField(
        max_length=100, unique=True, help_text="Identificador único de la transacción"
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=50,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    currency = models.CharField(max_length=10, default="USD")
    user = models.ForeignKey(
        User,
        related_name="orders",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.ForeignKey(
        Shipping, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Order {self.transaction_id} - {self.status}"


class OrderItem(TimeStampedUUIDModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.IntegerField()

    def __str__(self):
        if self.order:
            return f"Order {self.inventory.product.name} - {self.order.transaction_id}"
        return f"Order {self.inventory.product.name} - No Order"

    @cached_property
    def cost(self):
        """
        Total cost of the ordered item
        """
        return round(self.count * self.inventory.store_price, 2)
