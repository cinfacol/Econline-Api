from rest_framework import serializers
from .models import Cart, CartItem
from inventory.serializers import InventorySerializer
from coupons.serializers import CouponSerializer


class CartItemSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer()
    coupon = CouponSerializer()

    class Meta:
        model = CartItem
        fields = ("id", "cart", "coupon", "inventory", "count")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, source="cartitem_set")

    class Meta:
        model = Cart
        fields = ("id", "user", "total_items", "items")
