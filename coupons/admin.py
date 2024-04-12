from django.contrib import admin
from .models import Coupon, FixedPriceCoupon, PercentageCoupon


@admin.register(FixedPriceCoupon)
class FixedPriceCouponAdmin(admin.ModelAdmin):
    list_display = ["id", "discount_price", "uses"]


@admin.register(PercentageCoupon)
class PercentageCouponAdmin(admin.ModelAdmin):
    list_display = ["id", "discount_percentage", "uses"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "user",
        "fixed_price_coupon",
        "percentage_coupon",
        "content_type",
    ]
    list_filter = ["content_type"]
    search_fields = ["name"]
