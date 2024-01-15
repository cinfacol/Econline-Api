from django.contrib import admin

from .models import Product, ProductViews, Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["id", "alt_text", "image", "product", "created_at", "default"]


class MediaInline(admin.TabularInline):
    model = Media


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        MediaInline,
    ]
    list_display = [
        "pkid",
        "id",
        "title",
        "product_number",
        "category",
        "price",
        "product_type",
    ]
    list_filter = ["product_type"]


admin.site.register(ProductViews)
