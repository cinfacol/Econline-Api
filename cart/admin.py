from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total_items"]
    list_display_links = ["id", "user"]
    search_fields = ["id", "user__username"]
    list_filter = ["user"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", "coupon", "inventory"]
    search_fields = ["id", "cart__id", "coupon", "inventory_product__title"]
    list_filter = ["cart", "inventory"]
