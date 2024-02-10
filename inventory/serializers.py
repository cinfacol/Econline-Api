from attr import attributes
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import ManyToManyField

from django.db.models import Q
from rest_framework import serializers
from reviews.models import Review
from promotion.models import Promotion

from .models import (
    Brand,
    Category,
    Media,
    Attribute,
    AttributeValue,
    Product,
    Inventory,
    Stock,
    Type,
)


""" class AttributeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attribute
        fields = [
            "name",
            "description",
        ]
        depth = 2 """


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


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["name"]
        depth = 2


class ReviewSerializer(serializers.ModelSerializer):
    # product = serializers.SerializerMethodField()
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "rater",
            # "product",
            "inventory",
            "rating",
            "comment",
        )

    """ def get_product(self, obj):
        return obj.product.name
 """

    def get_inventory(self, obj):
        return obj.inventory.product.name


class ProductSerializer(serializers.ModelSerializer):
    # rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "ref_code",
            "category",
            "description",
            # "rating",
        ]
        read_only = True
        editable = False
        depth = 2

    """ def get_rating(self, obj):
        # return obj.reviews.product.name
        return ReviewSerializer(obj.Inventory_review.all(), many=True).data """


class MediaSerializer(serializers.ModelSerializer):
    inventory = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["id", "image", "inventory", "alt_text"]

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
    product = ProductSerializer(many=False, read_only=True)
    image = serializers.SerializerMethodField()
    brand = BrandSerializer(many=False, read_only=True)
    stock = StockSerializer(source="inventory_stock", read_only=True)
    type = TypeSerializer(read_only=True)
    attributes = AttributeValueSerializer(
        source="attribute_values", many=True, read_only=True
    )
    promotion_price = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            "id",
            "pkid",
            "sku",
            "upc",
            "product",
            # "user",
            "order",
            "brand",
            "type",
            "type_id",
            "attribute_values",
            "is_active",
            "is_default",
            "published_status",
            "retail_price",
            "store_price",
            "is_digital",
            "weight",
            "views",
            "stock",
            "image",
            "attributes",
            "updated_at",
            "created_at",
            "promotion_price",
            "rating",
        ]
        read_only = True
        depth = 3

    def get_image(self, obj):
        return MediaSerializer(obj.inventory_media.all(), many=True).data

    def get_rating(self, obj):
        # return obj.reviews.product.name
        return ReviewSerializer(obj.Inventory_review.all(), many=True).data

    def get_promotion_price(self, obj):

        try:
            x = Promotion.products_on_promotion.through.objects.get(
                Q(promotion_id__is_active=True) & Q(product_inventory_id=obj.id)
            )
            return x.promo_price
        except ObjectDoesNotExist:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        av_data = data.pop("attribute_values")
        attr_values = {}
        for key in av_data:
            attr_values.update({key["attribute"]["name"]: key["attribute"]})
        data.update({"specification": attr_values})

        return data


""" class ProductInventorySearchSerializer(serializers.ModelSerializer):

    product = ProductSerializer(many=False, read_only=True)
    brand = BrandSerializer(many=False, read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "sku",
            "store_price",
            "is_default",
            "product",
            "brand",
        ] """

""" class InventoryCategorySerializer(serializers.ModelSerializer):
    product_image = MediaSerializer(many=True)

    class Meta:
        model = Inventory
        fields = (
            "retail_price",
            "product_image",
        ) """


""" class ProductCategorySerializer(serializers.ModelSerializer):
    product_line = InventoryCategorySerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "pid",
            "created_at",
            "product_line",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        x = data.pop("product_line")

        if x:
            retail_price = x[0]["retail_price"]
            image = x[0]["product_image"]
            data.update({"retail_price": retail_price})
            data.update({"image": image})

        return data """
