from django.contrib import admin
from .models import Shipping


@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "time_to_delivery",
    )
    list_display_links = (
        "id",
        "name",
    )
    list_editable = ("price",)
    search_fields = ("name",)
    list_per_page = 25
