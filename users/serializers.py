from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source="profile.gender")
    profile_photo = serializers.ImageField(source="profile.profile_photo")
    top_agent = serializers.BooleanField(source="profile.top_agent")
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField(source="get_full_name")

    class Meta:
        model = User
        fields = [
            "pk",
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "profile_photo",
            "top_agent",
            "date_joined",
            "is_staff",
        ]

    def get_first_name(self, obj):
        return obj.first_name.title()

    def get_last_name(self, obj):
        return obj.last_name.title()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.is_superuser:
            representation["admin"] = True
        # También incluir información de staff/admin
        representation["is_admin"] = instance.is_staff or instance.is_superuser
        return representation


class CreateUserSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "password"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados al token si lo deseas
        token["email"] = user.email
        token["username"] = user.username
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_staff"] = user.is_staff
        token["is_admin"] = user.is_staff or user.is_superuser

        return token


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "user",
            "address_line_1",
            "address_line_2",
            "country_region",
            "city",
            "state_province_region",
            "postal_zip_code",
            "phone_number",
            "is_default",
        ]
