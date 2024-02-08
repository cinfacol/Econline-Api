from django.contrib import admin

from .models import Promotion, PromoType, Coupon
from .tasks import promotion_management, promotion_prices


class ProductOnPromotion(admin.StackedInline):
    model = Promotion.products_on_promotion.through
    extra = 4
    raw_id_fields = ("product_inventory_id",)


class InventoryList(admin.ModelAdmin):
    model = Promotion
    inlines = (ProductOnPromotion,)
    list_display = ("name", "is_active", "promo_start", "promo_end")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        promotion_prices.delay(obj.promo_reduction, obj.pkid)
        promotion_management.delay()


admin.site.register(Promotion, InventoryList)
admin.site.register(PromoType)
admin.site.register(Coupon)
