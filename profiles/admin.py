from django.contrib import admin

from .models import Profile, Address


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "pkid", "user", "gender"]
    list_filter = ["gender"]
    list_display_links = ["id", "pkid", "user"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "address",
        "phone_number",
        "country",
        "state",
        "city",
        "default",
    ]
    list_display_links = ["id", "address"]
