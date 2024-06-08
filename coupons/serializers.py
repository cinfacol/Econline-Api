from rest_framework import serializers
from .models import FixedPriceCoupon, PercentageCoupon, Coupon, Campaign


class FixedPriceCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixedPriceCoupon
        fields = ("id", "discount_price", "uses")


class PercentageCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = PercentageCoupon
        fields = ("id", "discount_percentage", "uses")


class CouponSerializer(serializers.ModelSerializer):
    fixed_price_coupon = FixedPriceCouponSerializer(required=False)
    percentage_coupon = PercentageCouponSerializer(required=False)

    class Meta:
        model = Coupon
        fields = (
            "id",
            "name",
            "user",
            "fixed_price_coupon",
            "percentage_coupon",
        )


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
