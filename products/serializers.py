from rest_framework import serializers

from .models import Product, ProductViews, Media
from ratings.models import Rating

# from categories.serializers import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    # category: CategorySerializer
    user = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()
    rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "user",
            "profile_photo",
            "title",
            "slug",
            "ref_code",
            "description",
            "product_number",
            "price",
            "tax",
            "final_product_price",
            "category",
            "product_type",
            "image",
            "published_status",
            "views",
            "rating",
        ]

    def get_user(self, obj):
        return obj.user.username

    def get_profile_photo(self, obj):
        return obj.user.profile.profile_photo.url

    def get_image(self, obj):
        return MediaSerializer(obj.imagenes.all(), many=True).data

    def get_rating(self, obj):
        return RatingSerializer(obj.product_review.all(), many=True).data


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ["updated_at", "pkid"]


class ProductViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductViews
        exclude = ["updated_at", "pkid"]


class MediaSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = (
            "image",
            "alt_text",
            "product",
            "is_featured",
            "default",
            "created_at",
            "updated_at",
        )

    def get_product(self, obj):
        return obj.product.title


class RatingSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = (
            "rater",
            "product",
            "rating",
            "comment",
        )

    def get_product(self, obj):
        return obj.product.title
