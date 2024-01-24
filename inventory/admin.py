from django.contrib import admin

from .models import (
    Product,
    Media,
    ProductInventory,
    Category,
    Brand,
    ProductAttribute,
    ProductType,
    ProductAttributeValue,
    Stock,
)


# admin.site.register(models.Category)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "parent"]
    list_display_links = ["id", "parent"]
    search_fields = ["name", "parent"]
    list_per_page = 25


class MediaInline(admin.TabularInline):
    model = Media


""" class ProductInventoryInline(admin.TabularInline):
    model = ProductInventory """


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ["attribute_value"]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["units", "units_sold"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """inlines = [
        ProductInventoryInline,
    ]"""

    list_display = [
        "id",
        "name",
        "category",
    ]
    list_filter = ["name"]


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    inlines = [
        MediaInline,
    ]
    list_display = ["product", "store_price"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]
