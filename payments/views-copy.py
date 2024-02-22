import stripe
from decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from inventory.models import Inventory


@api_view(["POST"])
def secret(request, format=None):
    if request.method == "POST":
        stripe.api_key = settings.STRIPE_SECRET
        user = request.data.get("user")
        cart = request.data.get("cart")

        tax_list = [0.115 if user["state"] == "PR" else 0]
        items = [c["name"] for c in cart]
        qty = [c["qty"] for c in cart]

        subtotal = []
        for i in cart:
            item_id = i.get("itemId")
            qty = i.get("qty")
            p = Inventory.objects.get(pk=item_id)

            # Validate inventory stock
            if p.stock == 0:
                return Response(
                    data={"message": "One of your products is sold out"},
                    status=status.HTTP_409_CONFLICT,
                )

            subtotal.append(p.price * qty)

        # total calculations
        tax = round(sum(subtotal) * Decimal(tax_list[0]), 2)
        total = round(Decimal(sum(subtotal) + tax), 2)
        stripe_total = int(total * 100)

        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )
        return Response(
            data={"tax": tax, "client_secret": intent.client_secret},
            status=status.HTTP_201_CREATED,
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)
