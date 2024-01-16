from django.contrib import admin

from .models import Rating


class RatingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "rater",
        "rating",
        "created_at",
    )
    list_display_links = (
        "id",
        "product",
    )
    list_filter = ("rating",)
    list_per_page = 20


admin.site.register(Rating, RatingAdmin)
