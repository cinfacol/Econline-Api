from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User, Address


class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = [
        "pkid",
        "id",
        "email",
        "username",
        "first_name",
        "last_name",
        "stripe_customer_id",
        "is_staff",
        "is_active",
    ]
    list_display_links = [
        "id",
        "email",
        "username",
    ]
    list_filter = [
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    ]
    fieldsets = (
        (
            _("Login Credentials"),
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            _("Personal Information"),
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            _("Permissions and Groups"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    search_fields = ["email", "username", "first_name", "last_name"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    model = Address
    list_display = [
        "pkid",
        "id",
        "user",
        "address_line_1",
        # "address_line_2",
        "city",
        "state_province_region",
        "is_default",
    ]
    list_display_links = [
        "id",
        "user",
    ]


admin.site.register(User, UserAdmin)
