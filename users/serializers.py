from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

# from rest_framework_simplejwt.tokens import RefreshToken, TokenError

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
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "gender",
            "profile_photo",
            "top_agent",
        ]

    def get_first_name(self, obj):
        return obj.first_name.title()

    def get_last_name(self, obj):
        return obj.last_name.title()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def to_representation(self, instance):
        representation = super(UserSerializer, self).to_representation(instance)
        if instance.is_superuser:
            representation["admin"] = True
        return representation


class CreateUserSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "password"]


# class LogoutUserSerializer(serializers.Serializer):
#     refresh_token = serializers.CharField()

#     default_error_message = {"bad_token": ("Token is expired or invalid")}

#     def validate(self, attrs):
#         self.token = attrs.get("refresh_token")

#         return attrs

#     def save(self, **kwargs):
#         try:
#             token = RefreshToken(self.token)
#             token.blacklist()
#         except TokenError:
#             return self.fail("bad_token")
