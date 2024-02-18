from django.contrib import admin

from .models import Cart


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total_items"]
    list_display_links = ["id", "user"]


# admin.site.register(Cart)
