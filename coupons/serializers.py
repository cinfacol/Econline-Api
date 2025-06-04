from rest_framework import serializers
from .models import FixedPriceCoupon, PercentageCoupon, Coupon, Campaign, CouponUsage
from categories.models import Category
from inventory.models import Inventory


class FixedPriceCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixedPriceCoupon
        fields = ("id", "discount_price", "uses")


class PercentageCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = PercentageCoupon
        fields = ("id", "discount_percentage", "uses")


class CouponUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponUsage
        fields = ("id", "coupon", "user", "order", "used_at", "discount_amount")
        read_only_fields = ("used_at",)


class CouponSerializer(serializers.ModelSerializer):
    fixed_price_coupon = FixedPriceCouponSerializer(required=False)
    percentage_coupon = PercentageCouponSerializer(required=False)
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )
    products = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Inventory.objects.all(), required=False
    )
    is_valid = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = (
            "id",
            "name",
            "code",
            "description",
            "fixed_price_coupon",
            "percentage_coupon",
            "start_date",
            "end_date",
            "min_purchase_amount",
            "max_discount_amount",
            "max_uses",
            "max_uses_per_user",
            "apply_to",
            "categories",
            "products",
            "is_active",
            "can_combine",
            "first_purchase_only",
            "is_valid",
            "remaining_uses",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_is_valid(self, obj):
        from django.utils import timezone

        now = timezone.now()
        return (
            obj.is_active
            and obj.start_date <= now <= obj.end_date
            and obj.max_uses > obj.used_by.count()
        )

    def get_remaining_uses(self, obj):
        return obj.max_uses - obj.used_by.count()


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "discount_type",
            "discount_rate",
            "discount_amount",
            "min_purchased_items",
            "apply_to",
            "target_product",
            "target_category",
            "created_at",
            "updated_at",
        ]
