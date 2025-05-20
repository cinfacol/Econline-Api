from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Payment, Subscription, SubscriptionHistory, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_user",
        "amount",
        "status",
        "payment_option",
        "created_at",
        "get_order_link",
    ]
    list_filter = ["status", "payment_option", "created_at"]
    search_fields = [
        "order__user__email",
        "order__user__first_name",
        "order__transaction_id",
    ]
    readonly_fields = ["stripe_session_id", "created_at", "updated_at"]

    def get_user(self, obj):
        return obj.order.user.email

    get_user.short_description = "Usuario"

    def get_order_link(self, obj):
        url = f"/admin/orders/order/{obj.order.id}"
        return format_html('<a href="{}">{}</a>', url, obj.order.transaction_id)

    get_order_link.short_description = "Orden"

    actions = ["process_refund"]

    @admin.action(description="Procesar reembolso para pagos seleccionados")
    def process_refund(self, request, queryset):
        for payment in queryset:
            if payment.status == Payment.PaymentStatus.COMPLETED:
                try:
                    # Lógica de reembolso
                    self.message_user(
                        request, f"Reembolso procesado para pago {payment.id}"
                    )
                except Exception as e:
                    self.message_user(
                        request, f"Error al procesar reembolso: {str(e)}", level="ERROR"
                    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "status",
        "current_period_start",
        "current_period_end",
        "cancel_at_period_end",
        "created_at",
    ]
    list_filter = ["status", "cancel_at_period_end", "created_at"]
    search_fields = ["user__email", "stripe_subscription_id"]
    readonly_fields = [
        "stripe_subscription_id",
        "stripe_customer_id",
        "current_period_start",
        "current_period_end",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Información básica", {"fields": ("user", "status", "stripe_price_id")}),
        (
            "Información de Stripe",
            {
                "fields": ("stripe_subscription_id", "stripe_customer_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Períodos",
            {
                "fields": (
                    "current_period_start",
                    "current_period_end",
                    "trial_start",
                    "trial_end",
                )
            },
        ),
        ("Estado de cancelación", {"fields": ("cancel_at_period_end", "canceled_at")}),
    )


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "subscription", "action", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = [
        "subscription__user__email",
        "subscription__stripe_subscription_id",
    ]
    readonly_fields = ["created_at"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["payment__order__user__email", "stripe_refund_id"]
    readonly_fields = ["stripe_refund_id", "created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el objeto ya existe
            return self.readonly_fields + ["payment", "amount"]
        return self.readonly_fields


class SubscriptionStatusFilter(admin.SimpleListFilter):
    title = "Estado de suscripción"
    parameter_name = "subscription_status"

    def lookups(self, request, model_admin):
        return Subscription.SubscriptionStatus.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
