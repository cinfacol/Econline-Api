from rest_framework import serializers
from .models import Cart, CartItem, DeliveryCost
from inventory.serializers import InventorySerializer
from coupons.serializers import CouponSerializer


class CartItemSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer()
    coupon = CouponSerializer()
    # cart = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "cart", "coupon", "inventory", "quantity")

    # def get_cart(self, obj):
    #     return obj.cart.id


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, source="cartitem_set")

    class Meta:
        model = Cart
        depth = 1
        fields = ("id", "user", "total_items", "items")


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
