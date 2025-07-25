import helpers
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimeStampedUUIDModel
from rest_framework.exceptions import ValidationError
from orders.models import Order
from users.models import User


class PaymentMethod(models.Model):
    key = models.CharField(
        max_length=10,
        unique=True,
        help_text="SC para Stripe Card, PP para PayPal, TR para transferencia PSE, CA para Cash",
    )
    label = models.CharField(
        max_length=50,
        help_text="Stripe Card para key SC, PayPal para key PP, Transferencia PSE para key TR, Cash para key CA",
    )
    icon_image = models.ImageField(
        verbose_name=_("Icon payment image"),
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.label


class Payment(TimeStampedUUIDModel):
    class PaymentStatus(models.TextChoices):
        PENDING = "P", _("Pendiente")
        COMPLETED = "C", _("Completado")
        FAILED = "F", _("Fallido")
        REFUNDED = "R", _("Reembolsado")
        CANCELLED = "X", _("Cancelado")

    order = models.ForeignKey(
        Order,
        related_name="payments",
        on_delete=models.CASCADE,
        help_text="Pedido asociado a este pago.",
    )
    user = models.ForeignKey(
        User,
        related_name="payments",
        on_delete=models.CASCADE,
        help_text="Usuario que realiza el pago.",
    )
    status = models.CharField(
        max_length=1,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        help_text="Estado del pago.",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
        help_text="Método de pago utilizado.",
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Monto total del pago."
    )
    currency = models.CharField(
        max_length=10, default="USD", help_text="Moneda del pago."
    )
    paid_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que el pago fue confirmado."
    )
    # IDs de gateway
    stripe_session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID de sesión de Stripe (checkout).",
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID de PaymentIntent de Stripe.",
    )
    paypal_transaction_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID de transacción de PayPal.",
    )
    external_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Referencia externa del pago (ej: número de recibo, referencia bancaria).",
    )
    # Breakdown
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto de impuestos incluidos en el pago.",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto de descuentos aplicados al pago.",
    )
    # Auditoría y trazabilidad
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Mensaje de error devuelto por el gateway, si aplica.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales del pago (gateway, cliente, etc.).",
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Indica si se ha enviado un correo electrónico de confirmación del pago.",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["payment_method"]),
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["paypal_transaction_id"]),
        ]

    def __str__(self):
        return f"Pago {self.id} - Pedido {self.order_id} - {self.get_status_display()}"

    def clean(self):
        # Validación: el monto debe ser positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("El monto del pago debe ser mayor a cero.")


class Refund(TimeStampedUUIDModel):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    stripe_refund_id = models.CharField(max_length=100, null=True, blank=True)
    paypal_refund_id = models.CharField(max_length=100, null=True, blank=True)
    reason = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    refunded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Reembolso {self.id} - Pago {self.payment_id}"


class Subscription(TimeStampedUUIDModel):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = "ACTIVE", _("Activa")
        CANCELED = "CANCELED", _("Cancelada")
        PAST_DUE = "PAST_DUE", _("Vencida")
        UNPAID = "UNPAID", _("No pagada")
        INCOMPLETE = "INCOMPLETE", _("Incompleta")
        TRIALING = "TRIALING", _("En prueba")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    paypal_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INCOMPLETE,
    )
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(default=timezone.now)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.status}"


class SubscriptionHistory(TimeStampedUUIDModel):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="history"
    )
    action = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]
