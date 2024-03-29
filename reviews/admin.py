from django.contrib import admin

from .models import Review


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "inventory",
        "rater",
        "rating",
        "created_at",
    )
    list_display_links = (
        "id",
        "inventory",
    )
    list_filter = ("rating",)
    list_per_page = 20


admin.site.register(Review, ReviewAdmin)
