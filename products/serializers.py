from rest_framework import serializers

from .models import Product
from categories.models import Category

# from reviews.models import Review

# from categories.serializers import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "ref_code",
            "category",
            "description",
            "is_active",
            "published_status",
        ]

    def create(self, validated_data):
        categories = validated_data.pop("category", [])
        product = Product.objects.create(**validated_data)
        product.category.set(categories)
        return product

    def update(self, instance, validated_data):
        categories = validated_data.pop("category", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.category.set(categories)
        return instance
