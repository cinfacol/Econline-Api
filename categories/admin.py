from django.contrib import admin

from .models import Category, MeasureUnit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "measure_unit"]
    list_display_links = ["id", "name"]
    search_fields = ["name"]
    list_per_page = 25


@admin.register(MeasureUnit)
class MeasureUnitAdmin(admin.ModelAdmin):
    list_display = ["id", "description"]
