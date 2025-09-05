from rest_framework import serializers

from orders.models import Order
from users.models import Address
from users.serializers import AddressSerializer

from .models import Payment, PaymentMethod, Subscription


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "key", "label", "icon_image", "is_active"]


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        source="payment_method",
        write_only=True,
        required=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_option_display = serializers.CharField(
        source="get_payment_option_display", read_only=True
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "user",
            "status",
            "status_display",
            "payment_method",
            "payment_method_id",
            "amount",
            "currency",
            "paid_at",
            "stripe_session_id",
            "stripe_payment_intent_id",
            "paypal_transaction_id",
            "external_reference",
            "tax_amount",
            "discount_amount",
            "error_message",
            "metadata",
            "created_at",
            "updated_at",
            "payment_option_display",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "user",
        ]


class PaymentTotalSerializer(serializers.Serializer):
    """Serializador para el cálculo de totales"""

    shipping_id = serializers.UUIDField(required=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    currency = serializers.CharField(read_only=True)


class CheckoutSessionSerializer(serializers.Serializer):
    """Serializador para crear sesión de checkout"""

    shipping_id = serializers.UUIDField(required=True)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        required=True,
        error_messages={
            "required": "Por favor selecciona un método de pago.",
            "does_not_exist": "Método de pago no válido.",
            "incorrect_type": "ID de método de pago inválido.",
        },
    )
    coupon_id = serializers.UUIDField(required=False, allow_null=True)
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Monto total calculado en el frontend",
    )
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Subtotal calculado en el frontend",
    )
    shipping_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Costo de envío calculado en el frontend",
    )
    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Descuento aplicado calculado en el frontend",
    )

    def validate(self, data):
        """
        Validación personalizada para asegurar que los valores decimales sean válidos
        """
        decimal_fields = ["total_amount", "subtotal", "shipping_cost", "discount"]

        for field in decimal_fields:
            if field in data and data[field] is not None:
                try:
                    # Convertir a Decimal para validar
                    from decimal import Decimal

                    Decimal(str(data[field]))
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        f"El campo {field} debe ser un número válido"
                    )

        return data


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializador para verificación de pagos"""

    status = serializers.ChoiceField(
        choices=Payment.PaymentStatus.choices, read_only=True
    )
    payment_method = PaymentMethodSerializer(read_only=True)


class PaymentOptionSerializer(serializers.ModelSerializer):
    buyer = serializers.CharField(source="order.user.get_full_name", read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "buyer",
            "status",
            "payment_method",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "order")


class CheckoutSerializer(serializers.ModelSerializer):
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
        address_data = validated_data.pop("address", None)
        payment_data = validated_data.pop("payment", None)

        # Update order fields
        instance = super().update(instance, validated_data)

        # Update or create address
        if address_data:
            address, created = Address.objects.get_or_create(
                shipping_orders=instance, defaults=address_data
            )
            if not created:
                for key, value in address_data.items():
                    setattr(address, key, value)
                address.save()
            instance.address = address
            instance.save()

        # Update or create payment
        if payment_data:
            payment, created = Payment.objects.get_or_create(
                order=instance, defaults=payment_data
            )
            if not created:
                for key, value in payment_data.items():
                    setattr(payment, key, value)
                payment.save()
            instance.payment = payment
            instance.save()

        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "trial_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
