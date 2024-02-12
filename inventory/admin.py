from django.contrib import admin

from .models import (
    Product,
    Media,
    Inventory,
    Category,
    MeasureUnit,
    Brand,
    Attribute,
    AttributeValue,
    Stock,
    Type,
)


class MediaInline(admin.TabularInline):
    model = Media


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "measure_unit"]
    list_display_links = ["id", "name"]
    search_fields = ["name"]
    list_per_page = 25


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


@admin.register(MeasureUnit)
class MeasureUnitAdmin(admin.ModelAdmin):
    list_display = ["id", "description"]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["id", "inventory", "units", "units_sold"]


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    exclude = ["id"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

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
        "pkid",
        "product",
        "store_price",
        "order",
        "sku",
    ]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]
