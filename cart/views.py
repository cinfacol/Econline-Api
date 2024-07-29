from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import JSONParser
from decimal import Decimal
import requests
from django.core.cache import cache
from django.conf import settings

from .models import Cart, CartItem, DeliveryCost
from coupons.models import Coupon
from .serializers import CartSerializer, CartItemSerializer, DeliveryCostSerializer
from inventory.models import Inventory
from inventory.serializers import InventorySerializer

taxes = settings.TAXES


class GetItemsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart = Cart.objects.get(user=user)
        cartId = cart.id
        total_items = cart.total_items
        # print("cartId", cart.id)

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {
                "cartId": cartId,
                "cart_items": serialized_cart_items,
                "total_items": total_items,
            },
            status=status.HTTP_200_OK,
        )


class GetTotalView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        data = JSONParser().parse(request)
        print("data", data)
        # Check for missing data and return error if necessary
        if not data or not data.get("items"):
            return Response(
                {"error": "Missing required data (items) in request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventories = []
        total_cost = Decimal(0)
        total_compare_cost = Decimal(0)
        tax_estimate = Decimal(0)
        shipping_estimate = Decimal(0)
        # finalPrice = Decimal(0)

        for item in data.get("items"):
            if item.get("inventory"):
                inventories.append(item)

        for object in inventories:
            inventory = object.get("inventory", {})  # Use default empty dict if missing
            coupon = object.get("coupon", None)
            # inventory = object["inventory"] if object["inventory"] else None
            # coupon = object["coupon"] if object["coupon"] else None

            if coupon:
                coupon_fixed_price_coupon = coupon.get("fixed_price_coupon")
                coupon_percentage_coupon = coupon.get("percentage_coupon")

                if coupon_fixed_price_coupon:
                    coupon_fixed_discount_price = coupon_fixed_price_coupon.get(
                        "discount_price"
                    )

                else:
                    coupon_fixed_discount_price = None

                if coupon_percentage_coupon:
                    coupon_discount_percentage = coupon_percentage_coupon.get(
                        "discount_percentage"
                    )

                else:
                    coupon_discount_percentage = None
            else:
                coupon_fixed_price_coupon = None
                coupon_fixed_discount_price = None
                coupon_percentage_coupon = None
                coupon_discount_percentage = None

            inventory_price = inventory.get("price")
            inventory_compare_price = inventory.get("compare_price", inventory_price)
            inventory_discount = inventory.get("discount", False)

            # Calculate Total Cost Without Discounts and Coupons and Taxes (total_cost)
            """ if inventory_discount == False:
                total_cost += Decimal(inventory_price)
            else:
                total_cost += Decimal(inventory_compare_price)

            # Calculate Total Cost With Discount and Coupons if present (total_compare_cost)
            if inventory_discount == True:
                if coupon_fixed_discount_price is not None:
                    total_compare_cost += max(
                        Decimal(inventory_compare_price)
                        - Decimal(coupon_fixed_discount_price),
                        0,
                    )
                elif coupon_discount_percentage is not None:
                    total_compare_cost += Decimal(inventory_compare_price) * (
                        1 - (Decimal(coupon_discount_percentage) / 100)
                    )
                else:
                    total_compare_cost += Decimal(inventory_compare_price)
            else:
                if coupon_fixed_discount_price is not None:
                    total_compare_cost += max(
                        Decimal(inventory_price) - Decimal(coupon_fixed_discount_price),
                        0,
                    )
                elif coupon_discount_percentage is not None:
                    total_compare_cost += Decimal(inventory_price) * (
                        1 - (Decimal(coupon_discount_percentage) / 100)
                    )
                else:
                    total_compare_cost += Decimal(inventory_price)

            # Calculate Taxes for Total Cost (tax_estimate)
            tax_estimate = Decimal(total_compare_cost) * Decimal(taxes)
            # print('Tax Estimate: ',tax_estimate )
            finalinventoryPrice = Decimal(total_compare_cost) + Decimal(tax_estimate)

        finalPrice = Decimal(finalinventoryPrice) """
            # Calculate total cost based on discounts
            if inventory_discount:
                discount_price = coupon.get("fixed_price_coupon", {}).get(
                    "discount_price"
                )
                discount_percentage = coupon.get("percentage_coupon", {}).get(
                    "discount_percentage"
                )
                total_compare_cost += max(
                    (
                        inventory_compare_price - discount_price
                        if discount_price
                        else (
                            inventory_compare_price * (1 - discount_percentage / 100)
                            if discount_percentage
                            else inventory_compare_price
                        )
                    ),
                    0,
                )
            else:
                total_compare_cost += inventory_price

            total_cost += (
                inventory_compare_price  # Accumulate total cost regardless of discounts
            )

        # Calculate tax estimate
        tax_estimate = Decimal(total_compare_cost) * Decimal(taxes)

        final_price = Decimal(total_compare_cost) + Decimal(tax_estimate)

        return Response(
            {
                "total_cost": total_cost,
                "total_compare_cost": total_compare_cost,
                "finalPrice": final_price,
                "tax_estimate": tax_estimate,
                "shipping_estimate": shipping_estimate,  # Include shipping estimate if available
                # "total_cost": total_cost,
                # "total_compare_cost": total_compare_cost,
                # "finalPrice": finalPrice,
                # "tax_estimate": tax_estimate,
                # "shipping_estimate": shipping_estimate,
            },
            status=status.HTTP_200_OK,
        )


class AddItemToCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data

        item_id = data["inventory_id"]  # inventory's id to add
        coupon_id = (
            data.get("coupon", {}).get("id") if data.get("coupon").get("id") else None
        )
        quantity = data["quantity"]
        cart, created = Cart.objects.get_or_create(user=user)

        total_items = cart.total_items or 0

        inventory = Inventory.objects.get(id=item_id)

        # Check if item already in cart
        if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
            return Response(
                {"error": "Item is already in cart"},
                status=status.HTTP_409_CONFLICT,
            )

        cart_item_object = CartItem.objects.create(
            inventory=inventory, cart=cart, quantity=quantity, coupon=coupon_id
        )

        if data.get("coupon").get("id") is not None:
            # Get the coupon object
            coupon = Coupon.objects.get(id=coupon_id)

            # Validate that the coupon applies to the inventory
            if coupon.inventory != inventory:
                return Response(
                    {"error": "Coupon does not apply to this inventory"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item_object.coupon = coupon
            cart_item_object.save()

        if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
            # Update the total number of items in the cart
            total_items = int(cart.total_items) + 1
            Cart.objects.filter(user=user).update(total_items=total_items)

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {"cart": serialized_cart_items, "total_items": total_items},
            status=status.HTTP_200_OK,
        )


class RemoveItemView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        inventory_id = request.data
        item_id = inventory_id

        cart, _ = Cart.objects.get_or_create(user=user)

        inventory = Inventory.objects.get(id=item_id)
        cart_item = CartItem.objects.filter(cart=cart, inventory=inventory)

        if not cart_item.exists():
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        # Update the total number of items in the cart
        total_items = max(0, int(cart.total_items) - 1)
        Cart.objects.filter(user=user).update(total_items=total_items)

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {"cart": serialized_cart_items, "total_items": total_items},
            status=status.HTTP_200_OK,
        )


class ClearCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items.delete()
        cart.total_items = 0
        cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SynchCartItemsView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, format=None):
        items = []
        inventories = []
        # products = []
        # tiers = []

        data = request.data

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = data["items"]

        # Clear all existing items in the cart
        cart.cartitem_set.all().delete()

        for item in cart_items:
            inventories.append(item)

        # Add inventories to the cart
        for inventory_data in inventories:
            inventory = Inventory.objects.get(id=inventory_data["inventory"]["id"])

            coupon_id = inventory_data.get("coupon").get("id")
            if coupon_id is not None:
                coupon = Coupon.objects.get(id=coupon_id)
            else:
                coupon = None

            # create and save the cart item
            item = CartItem(
                cart=cart,
                inventory=inventory,
                coupon=coupon,
                referrer=inventory_data.get("referrer"),
            )
            item.save()

            items.append(item)

        # calculate total_items based on newly added items
        cart.total_items = CartItem.objects.filter(cart=cart).quantity()
        cart.save()

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {"cart": serialized_cart_items, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class DeliveryCostListAPIView(APIView):
    """
    API endpoint for listing and creating delivery costs.
    """

    def get(self, request):
        delivery_costs = DeliveryCost.objects.all().order_by("id")
        serializer = DeliveryCostSerializer(delivery_costs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DeliveryCostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeliveryCostDetailAPIView(APIView):
    """
    API endpoint for retrieving, updating, and deleting a specific delivery cost.
    """

    def get_object(self, pk):
        try:
            return DeliveryCost.objects.get(pk=pk)
        except DeliveryCost.DoesNotExist:
            return None

    def get(self, request, pk):
        delivery_cost = self.get_object(pk)
        if not delivery_cost:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryCostSerializer(delivery_cost)
        return Response(serializer.data)

    def put(self, request, pk):
        delivery_cost = self.get_object(pk)
        if not delivery_cost:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = DeliveryCostSerializer(delivery_cost, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        delivery_cost = self.get_object(pk)
        if not delivery_cost:
            return Response(status=status.HTTP_404_NOT_FOUND)
        delivery_cost.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
