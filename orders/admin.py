from django.contrib import admin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "id",
        "transaction_id",
        "amount",
        "status",
    )
    list_display_links = (
        "id",
        "transaction_id",
    )
    list_filter = ("status",)
    list_editable = ("status",)
    list_per_page = 25


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "id",
        "name",
        "inventory",
        "order",
        "price",
        "count",
    )
    list_display_links = (
        "id",
        "name",
    )
    list_per_page = 25
