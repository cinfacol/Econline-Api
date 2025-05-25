from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Payment, PaymentMethod, Subscription, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "user",
        "status",
        "payment_option",
        "amount",
        "currency",
        "paid_at",
        "stripe_payment_intent_id",
        "paypal_transaction_id",
        "external_reference",
    )
    list_filter = ("status", "payment_option", "currency")
    search_fields = (
        "id",
        "order__id",
        "user__email",
        "stripe_payment_intent_id",
        "paypal_transaction_id",
        "external_reference",
    )
    readonly_fields = ("created_at", "updated_at", "error_message", "metadata")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "user",
                    "status",
                    "payment_option",
                    "amount",
                    "currency",
                    "paid_at",
                    "stripe_session_id",
                    "stripe_payment_intent_id",
                    "paypal_transaction_id",
                    "external_reference",
                    "tax_amount",
                    "discount_amount",
                    "error_message",
                    "metadata",
                )
            },
        ),
        ("Tiempos", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "method_type",
        "card_last4",
        "card_brand",
        "expires_at",
        "is_default",
        "status",
    )
    search_fields = ("user__email", "card_last4", "gateway_payment_method_id")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "user",
        "amount",
        "currency",
        "status",
        "refunded_at",
    )
    search_fields = (
        "payment__id",
        "user__email",
        "stripe_refund_id",
        "paypal_refund_id",
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan_id",
        "amount",
        "currency",
        "status",
        "current_period_start",
        "current_period_end",
    )
    search_fields = (
        "user__email",
        "plan_id",
        "stripe_subscription_id",
        "paypal_subscription_id",
    )
