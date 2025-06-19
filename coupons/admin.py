from django.contrib import admin
from .models import Coupon, FixedPriceCoupon, PercentageCoupon, Campaign, CouponUsage


@admin.register(FixedPriceCoupon)
class FixedPriceCouponAdmin(admin.ModelAdmin):
    list_display = ["id", "discount_price", "uses"]
    search_fields = ["discount_price"]


@admin.register(PercentageCoupon)
class PercentageCouponAdmin(admin.ModelAdmin):
    list_display = ["id", "discount_percentage", "uses"]
    search_fields = ["discount_percentage"]


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ["id", "coupon", "user", "order", "used_at", "discount_amount"]
    list_filter = ["used_at", "coupon"]
    search_fields = ["user__email", "coupon__name", "order__id"]
    date_hierarchy = "used_at"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "description",
        "apply_to",
        "start_date",
        "end_date",
        "is_active",
        "min_purchase_amount",
        "max_uses",
        "max_uses_per_user",
    ]
    list_filter = [
        "is_active",
        "apply_to",
        "start_date",
        "end_date",
        "first_purchase_only",
        "can_combine",
    ]
    search_fields = ["name", "code", "description"]
    filter_horizontal = ["categories", "products"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Información Básica",
            {"fields": ("name", "code", "description", "is_active")},
        ),
        (
            "Descuento",
            {
                "fields": (
                    "fixed_price_coupon",
                    "percentage_coupon",
                    "max_discount_amount",
                )
            },
        ),
        ("Restricciones de Tiempo", {"fields": ("start_date", "end_date")}),
        (
            "Restricciones de Uso",
            {"fields": ("min_purchase_amount", "max_uses", "max_uses_per_user")},
        ),
        ("Alcance", {"fields": ("apply_to", "categories", "products")}),
        (
            "Restricciones Adicionales",
            {"fields": ("can_combine", "first_purchase_only")},
        ),
        ("Seguimiento", {"fields": ("created_by", "created_at", "updated_at")}),
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "discount_type",
        "discount_rate",
        "discount_amount",
        "min_purchased_items",
        "apply_to",
        "target_product",
        "target_category",
    ]
    list_filter = ["discount_type", "apply_to"]
    search_fields = ["target_product__name", "target_category__name"]
