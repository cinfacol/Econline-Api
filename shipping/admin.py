from django.contrib import admin

from .models import Shipping


@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "service_type",
        "transport_type",
        "standard_shipping_cost",
        "free_shipping_threshold",
        "is_active",
        "is_default",
        "time_to_delivery",
    )
    list_filter = ("service_type", "transport_type", "is_active", "is_default")
    search_fields = ("name", "service_type", "transport_type")
    list_editable = ("is_active", "is_default")
    fieldsets = (
        ("Información Básica", {"fields": ("name", "time_to_delivery", "is_active")}),
        ("Tipo de Servicio", {"fields": ("service_type", "transport_type")}),
        (
            "Configuración de Costos",
            {
                "fields": ("standard_shipping_cost", "free_shipping_threshold"),
                "description": "Configuración de costos de envío y umbral para envío gratuito",
            },
        ),
    )
    ordering = ("-is_default", "name")
