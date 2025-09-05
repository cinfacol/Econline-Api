from rest_framework import serializers

from coupons.serializers import CouponSerializer
from inventory.serializers import InventorySerializer

from .models import Cart, CartItem, DeliveryCost


class CartItemSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer()

    class Meta:
        model = CartItem
        fields = ["id", "cart", "inventory", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)  # Include coupon serializer

    class Meta:
        model = Cart
        depth = 1
        fields = ["id", "user", "total_items", "items", "coupon"]  # Add 'coupon' field


class DeliveryCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCost
        fields = [
            "id",
            "status",
            "cost_per_delivery",
            "cost_per_product",
            "fixed_cost",
            "created_at",
            "updated_at",
        ]
