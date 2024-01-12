from django.contrib import admin

from .models import Rating


class RatingAdmin(admin.ModelAdmin):
    list_display = ["rater", "product", "rating"]


admin.site.register(Rating, RatingAdmin)
