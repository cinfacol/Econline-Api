from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "id",
        "name",
        "slug",
        "ref_code",
        "is_active",
        "published_status",
        "get_categories",
    ]
    list_filter = ["is_active", "published_status", "category"]
    search_fields = ["name", "ref_code", "description"]
    readonly_fields = ["slug", "ref_code"]

    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.category.all()])

    get_categories.short_description = "Categories"
