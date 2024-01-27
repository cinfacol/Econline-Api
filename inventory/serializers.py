from attr import attributes
from django.core.exceptions import ObjectDoesNotExist

# from django.db.models import Q
from rest_framework import serializers

from .models import (
    Brand,
    Category,
    Media,
    Attribute,
    AttributeValue,
    Product,
    Inventory,
    Stock,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "slug", "is_active"]
        read_only = True


class MediaSerializer(serializers.ModelSerializer):
    img_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ["img_url", "alt_text"]
        read_only = True
        editable = False

    def get_img_url(self, obj):
        return obj.img_url.url


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ("id", "inventory", "units", "units_sold")


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ("name", "id")


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute = AttributeSerializer(many=False)

    class Meta:
        model = AttributeValue
        fields = (
            "attribute",
            "value",
        )


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["name"]
        read_only = True


class ProductSerializer(serializers.ModelSerializer):
    # product_line = InventorySerializer(many=True)
    # attribute_value = AttributeValueSerializer(many=True)

    class Meta:
        model = Product
        read_only = True
        editable = False
        fields = [
            "name",
            "slug",
            "pid",
            "user",
            "description",
            # "product_line",
            # "attribute_value",
        ]

    """ def to_representation(self, instance):
        data = super().to_representation(instance)
        av_data = data.pop("attribute_value")
        attr_values = {}
        for key in av_data:
            attr_values.update({key["attribute"]["name"]: key["attribute_value"]})
        data.update({"attribute": attr_values})

        return data """


class InventorySerializer(serializers.ModelSerializer):
    # attribute_value = AttributeValueSerializer(many=True)
    # product_image = MediaSerializer(many=True)
    # stock = StockSerializer()
    product = ProductSerializer(many=False, read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    stock = StockSerializer(read_only=True)
    attributes = AttributeValueSerializer(
        source="attribute_values", many=True, read_only=True
    )
    # promotion_price = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            "id",
            "sku",
            "upc",
            "store_price",
            "is_default",
            "stock",
            "order",
            "media",
            "attributes",
            # "promotion_price",
        ]
        read_only = True

    """ def get_promotion_price(self, obj):

        try:
            x = Promotion.products_on_promotion.through.objects.get(
                Q(promotion_id__is_active=True) & Q(product_inventory_id=obj.id)
            )
            return x.promo_price
        except ObjectDoesNotExist:
            return None """

    """ def to_representation(self, instance):
        data = super().to_representation(instance)
        av_data = data.pop("attribute_value")
        attr_values = {}
        for key in av_data:
            attr_values.update({key["attribute"]["name"]: key["attribute_value"]})
        data.update({"specification": attr_values})

        return data """


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
