from django.core.exceptions import ObjectDoesNotExist

from django.db.models import Q, Avg, Count
from rest_framework import serializers
from reviews.models import Review
from promotion.models import Promotion
from products.serializers import ProductSerializer
from users.serializers import UserSerializer
from .models import (
    Brand,
    Media,
    AttributeValue,
    InventoryViews,
    Inventory,
    Stock,
    Type,
)


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        depth = 2
        fields = [
            "attribute",
            "value",
        ]
        read_only = True


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["name"]


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ["name"]


class ReviewSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "rater",
            "inventory",
            "rating",
            "comment",
        )
        depth = 1

    def get_inventory(self, obj):
        return obj.inventory.product.name


class InventoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryViews
        exclude = ["updated_at", "pkid"]


class MediaSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["id", "image", "inventory", "alt_text", "is_featured", "default"]

    def get_inventory(self, obj):
        return obj.inventory.product.name


class StockSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ("id", "inventory", "units", "units_sold")

    def get_inventory(self, obj):
        return obj.units


class InventorySerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False, read_only=True)
    product = ProductSerializer(many=False, read_only=True)
    image = serializers.SerializerMethodField()
    brand = BrandSerializer(many=False, read_only=True)
    stock = StockSerializer(source="inventory_stock", read_only=True)
    type = TypeSerializer(read_only=True)
    """ attributes = AttributeValueSerializer(
        source="attribute_values", many=True, read_only=True
    ) """
    promotion_price = serializers.SerializerMethodField()
    # rating = serializers.SerializerMethodField() # Reemplazado por average_rating y rating_count
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            "id",
            "pkid",
            "sku",
            "upc",
            "product",
            "user",
            "brand",
            "type",
            "quality",
            "attribute_values",
            "is_active",
            "is_default",
            "published_status",
            "retail_price",
            "store_price",
            "taxe",
            "promotion_price",
            "is_digital",
            "weight",
            "views",
            "stock",
            "image",
            # "attributes",
            "updated_at",
            "created_at",
            # "rating", # Reemplazado
            "average_rating",
            "rating_count",
        ]
        read_only = True
        depth = 3

    # def get_user(self, obj):
    #     return obj.user.username

    def get_image(self, obj):
        return MediaSerializer(obj.inventory_media.all(), many=True).data

    # def get_rating(self, obj): # Reemplazado por get_average_rating y get_rating_count
    #     return ReviewSerializer(obj.Inventory_review.all(), many=True).data

    def get_average_rating(self, obj):
        # Calcula el promedio usando agregación de BD. Devuelve None si no hay reviews.
        # El '.get("rating__avg")' maneja el caso None si no hay reviews.
        # Redondeamos a 1 decimal si no es None.
        avg = obj.Inventory_review.aggregate(Avg("rating")).get("rating__avg")
        return round(avg, 1) if avg is not None else 0  # Devolver 0 si no hay reviews

    def get_rating_count(self, obj):
        # Calcula la cuenta usando agregación de BD.
        return obj.Inventory_review.aggregate(Count("id")).get("id__count")

    def get_promotion_price(self, obj):

        try:
            x = Promotion.products_on_promotion.through.objects.get(
                Q(promotion_id__is_active=True) & Q(product_inventory_id__id=obj.id)
            )
            return x.promo_price
        except ObjectDoesNotExist:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        av_data = data.pop("attribute_values")
        attr_values = {}
        for key in av_data:
            attr_values.update({key["attribute"]["name"]: key["value"]})
        data.update({"specification": attr_values})

        return data


class InventoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        exclude = ["updated_at", "pkid"]
