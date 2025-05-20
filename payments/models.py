from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedUUIDModel
from orders.models import Order
from users.models import User


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
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Payment {self.id}"


class PaymentMethod(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_payment_method_id = models.CharField(max_length=100)
    card_last4 = models.CharField(max_length=4)
    card_brand = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)


class Refund(TimeStampedUUIDModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_refund_id = models.CharField(max_length=100)
    reason = models.CharField(max_length=50)
    status = models.CharField(max_length=20)


class Subscription(TimeStampedUUIDModel):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        CANCELED = "CANCELED", _("Canceled")
        PAST_DUE = "PAST_DUE", _("Past Due")
        UNPAID = "UNPAID", _("Unpaid")
        INCOMPLETE = "INCOMPLETE", _("Incomplete")
        TRIALING = "TRIALING", _("Trialing")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    stripe_subscription_id = models.CharField(max_length=100)
    stripe_customer_id = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INCOMPLETE,
    )
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.stripe_subscription_id}"


class SubscriptionHistory(TimeStampedUUIDModel):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="history"
    )
    action = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]
