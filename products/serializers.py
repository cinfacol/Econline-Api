from rest_framework import serializers

from .models import Product, ProductViews, Media

# from categories.serializers import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    # category: CategorySerializer
    user = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()
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
        ]

    def get_user(self, obj):
        return obj.user.username

    def get_profile_photo(self, obj):
        return obj.user.profile.profile_photo.url

    def get_image(self, obj):
        return MediaSerializer(obj.imagenes.all(), many=True).data


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
