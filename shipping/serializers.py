from decimal import Decimal

from rest_framework import serializers

from .models import Shipping


class ShippingSerializer(serializers.ModelSerializer):
    is_free_shipping = serializers.SerializerMethodField()
    estimated_delivery_days = serializers.SerializerMethodField()

    class Meta:
        model = Shipping
        fields = [
            "id",
            "name",
            "service_type",
            "transport_type",
            "standard_shipping_cost",
            "free_shipping_threshold",
            "is_active",
            "is_default",
            "time_to_delivery",
            "is_free_shipping",
            "estimated_delivery_days",
        ]
        read_only_fields = ["id"]

    def get_is_free_shipping(self, obj):
        """
        Calcula si el envío es gratuito basado en el total de la orden
        """
        order_total = self.context.get("order_total", Decimal("0"))
        return order_total >= obj.free_shipping_threshold

    def get_estimated_delivery_days(self, obj):
        """
        Obtiene los días estimados de entrega
        """
        return obj.get_estimated_delivery_days()


class ShippingCalculationSerializer(serializers.Serializer):
    order_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.00"), required=True
    )
    shipping_id = serializers.UUIDField(required=False)
    weight = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
        default=Decimal("1.0"),
    )
    origin_code = serializers.CharField(required=False)
