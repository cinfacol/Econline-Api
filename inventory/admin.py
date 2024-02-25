from django.contrib import admin

from .models import (
    Media,
    Inventory,
    Brand,
    Attribute,
    AttributeValue,
    Stock,
    Type,
    InventoryViews,
)


class MediaInline(admin.TabularInline):
    model = Media


class MediaInline(admin.TabularInline):
    model = Media


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue


class StockInline(admin.TabularInline):
    model = Stock


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    inlines = [
        AttributeValueInline,
    ]
    list_display = ["name", "description"]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "inventory", "units", "units_sold"]


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    exclude = ["id"]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    inlines = [
        MediaInline,
        StockInline,
    ]
    list_display = [
        "pkid",
        "id",
        "product",
        "quality",
        "store_price",
        # "order",
        "sku",
    ]
    list_display_links = ["pkid", "id", "product"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(InventoryViews)
class InventoryViewsAdmin(admin.ModelAdmin):
    list_display = ["inventory", "ip"]


# admin.site.register(InventoryViews)
