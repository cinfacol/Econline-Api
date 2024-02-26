# from django_countries.serializer_fields import CountryField
from rest_framework import serializers

from reviews.serializers import ReviewSerializer

from .models import Profile, Address


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    full_name = serializers.SerializerMethodField(read_only=True)
    address = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "id",
            "profile_photo",
            "about_me",
            "license",
            "gender",
            "address",
            "is_buyer",
            "is_seller",
            "is_agent",
            "num_reviews",
        ]

    def get_full_name(self, obj):
        first_name = obj.user.first_name.title()
        last_name = obj.user.last_name.title()
        return f"{first_name} {last_name}"

    def get_address(self, obj):
        return AddressSerializer(obj.profile_address.all(), many=True).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.top_agent:
            representation["top_agent"] = True
        return representation


class UpdateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = [
            "profile_photo",
            "about_me",
            "license",
            "gender",
            "is_buyer",
            "is_seller",
            "is_agent",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.top_agent:
            representation["top_agent"] = True
        return representation


class AddressSerializer(serializers.ModelSerializer):
    # country = CountryField(name_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = [
            "profile",
            "phone_number",
            "country",
            "state",
            "city",
            "zip_code",
            "default",
        ]

    def get_profile(self, obj):
        return obj.profile.user.username


class UpdateAddressSerializer(serializers.ModelSerializer):
    # country = CountryField(name_only=True)

    class Meta:
        model = Address
        fields = [
            "address",
            "phone_number",
            "country",
            "state",
            "city",
            "default",
        ]
