from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedUUIDModel
from orders.models import Order


class Payment(TimeStampedUUIDModel):
    PENDING = "P"
    COMPLETED = "C"
    FAILED = "F"

    STATUS_CHOICES = (
        (PENDING, _("pending")),
        (COMPLETED, _("completed")),
        (FAILED, _("failed")),
    )

    # Payment options
    PAYPAL = "P"
    STRIPE = "S"

    PAYMENT_CHOICES = ((PAYPAL, _("paypal")), (STRIPE, _("stripe")))

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PENDING)
    payment_option = models.CharField(max_length=1, choices=PAYMENT_CHOICES)
    order = models.OneToOneField(
        Order, related_name="payment", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.order.user.get_full_name()
