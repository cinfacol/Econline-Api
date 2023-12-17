from django_countries.serializer_fields import CountryField
from rest_framework import fields, serializers

# from apps.ratings.serializers import RatingSerializer

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    full_name = serializers.SerializerMethodField(read_only=True)
    country = CountryField(name_only=True)
    reviews = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "id",
            "phone_number",
            "profile_photo",
            "about_me",
            "address_line_1",
            "address_line_2",
            "license",
            "gender",
            "country",
            "departamento",
            "city",
            "zipcode",
            "is_buyer",
            "is_seller",
            "is_agent",
            "rating",
            "num_reviews",
            "reviews",
        ]

    def get_full_name(self, obj):
        first_name = obj.user.first_name.title()
        last_name = obj.user.last_name.title()
        return f"{first_name} {last_name}"

    """ def get_reviews(self, obj):
        reviews = obj.agent_review.all()
        serializer = RatingSerializer(reviews, many=True)
        return serializer.data """

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.top_agent:
            representation["top_agent"] = True
        return representation


class UpdateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    # Profile_photo = serializers.ImageField(required=False)
    # country = CountryField(name_only=True)

    class Meta:
        model = Profile
        fields = [
            "username",
            "phone_number",
            "profile_photo",
            "about_me",
            "address_line_1",
            "address_line_2",
            "gender",
            "country",
            "departamento",
            "city",
            "zipcode",
        ]

    def update(self, instance, validated_data):
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.profile_photo = validated_data.get(
            "profile_photo", instance.profile_photo
        )
        instance.about_me = validated_data.get("about_me", instance.about_me)
        instance.address_line_1 = validated_data.get(
            "address_line_1", instance.address_line_1
        )
        instance.address_line_2 = validated_data.get(
            "address_line_2", instance.address_line_2
        )
        instance.license = validated_data.get("license", instance.license)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.country = validated_data.get("country", instance.country)
        instance.departamento = validated_data.get(
            "departamento", instance.departamento
        )
        instance.city = validated_data.get("city", instance.city)
        instance.zipcode = validated_data.get("zipcode", instance.zipcode)

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.top_agent:
            representation["top_agent"] = True
        return representation
