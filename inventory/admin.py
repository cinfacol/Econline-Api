from django.contrib import admin

from .models import (
    Product,
    Media,
    Inventory,
    Category,
    Brand,
    Attribute,
    AttributeValue,
    Stock,
)


# admin.site.register(models.Category)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id"]
    search_fields = ["name"]
    list_per_page = 25


class MediaInline(admin.TabularInline):
    model = Media


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue


class StockInline(admin.TabularInline):
    model = Stock


""" class InventoryInline(admin.TabularInline):
    model = Inventory """


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    inlines = [
        AttributeValueInline,
    ]
    list_display = ["name", "description"]


""" @admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ["value"] """


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "units", "units_sold"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """inlines = [
        ProductInventoryInline,
    ]"""

    list_display = [
        "id",
        "name",
    ]
    list_filter = ["name"]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    inlines = [
        MediaInline,
        StockInline,
    ]
    list_display = [
        "product",
        "store_price",
        "order",
        "sku",
    ]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]
