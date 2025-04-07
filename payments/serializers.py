from rest_framework import serializers

from orders.models import Order
from payments.models import Payment
from users.models import Address
from users.serializers import AddressSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer to CRUD payments for an order.
    """

    buyer = serializers.CharField(source="order.user.get_full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'status',
            'payment_option',
            'order',
            'amount',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['status', 'stripe_session_id']

class PaymentTotalSerializer(serializers.Serializer):
    """Serializador para el cálculo de totales"""
    shipping_id = serializers.UUIDField(required=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True)

class CheckoutSessionSerializer(serializers.Serializer):
    """Serializador para crear sesión de checkout"""
    shipping_id = serializers.UUIDField(required=True)
    payment_option = serializers.ChoiceField(
        choices=Payment.PAYMENT_CHOICES,
        required=True
    )

class PaymentVerificationSerializer(serializers.Serializer):
    """Serializador para verificación de pagos"""
    status = serializers.ChoiceField(
        choices=Payment.STATUS_CHOICES,
        read_only=True
    )
    payment_option = serializers.ChoiceField(
        choices=Payment.PAYMENT_CHOICES,
        read_only=True
    )


class PaymentOptionSerializer(serializers.ModelSerializer):
    """
    Payment serializer for checkout. Order will be automatically set during checkout.
    """

    buyer = serializers.CharField(source="order.user.get_full_name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "buyer",
            "status",
            "payment_option",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "order")


class CheckoutSerializer(serializers.ModelSerializer):
    """
    Serializer class to set or update shipping address, billing address and payment of an order.
    """

    address = AddressSerializer()
    payment = PaymentOptionSerializer()

    class Meta:
        model = Order
        fields = (
            "id",
            "payment",
            "address",
            "billing_address",
        )

    def update(self, instance, validated_data):
        order_address = None
        order_billing_address = None
        order_payment = None

        address = validated_data["address"]

        # Shipping address for an order is not set
        if not instance.address:
            order_address = Address(**address)
            order_address.save()
        else:
            # Shipping address for an order is already set so update its value
            address = Address.objects.filter(shipping_orders=instance.id)
            address.update(**address)

            order_address = address.first()

        payment = validated_data["payment"]

        # Payment option is not set for an order
        if not instance.payment:
            order_payment = Payment(**payment, order=instance)
            order_payment.save()

        else:
            # Payment option is set so update its value
            p = Payment.objects.filter(order=instance)
            p.update(**payment)

            order_payment = p.first()

        # Update order
        instance.address = order_address
        instance.payment = order_payment
        instance.save()

        return instance
