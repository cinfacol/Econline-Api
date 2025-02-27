from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms

from .models import User, Address


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = ["email", "username", "first_name", "last_name"]
        error_class = "error"


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name"]
        error_class = "error"


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "address_line_1",
            "address_line_2",
            "country_region",
            "city",
            "state_province_region",
            "postal_zip_code",
            "phone_number",
            "is_default",
        ]
        error_class = "error"
