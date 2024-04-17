from rest_framework_api.views import StandardAPIView
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from decimal import Decimal
import requests
from django.core.cache import cache
from django.conf import settings

from .models import Cart, CartItem
from coupons.models import Coupon
from .serializers import CartSerializer, CartItemSerializer
from inventory.models import Inventory
from inventory.serializers import InventorySerializer

taxes = settings.TAXES


class GetItemsView(StandardAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart = Cart.objects.get(user=user)

        total_items = cart.total_items

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return self.send_response(
            {
                "cart_items": serialized_cart_items,
                "total_items": total_items,
            },
            status=status.HTTP_200_OK,
        )


class GetTotalView(StandardAPIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        data = JSONParser().parse(request)
        if not data:
            return self.send_response(
                {
                    "total_cost": 0,
                    # "total_cost_ethereum": 0,
                    # "maticCost": 0,
                    "total_compare_cost": 0,
                    "finalPrice": 0,
                    "tax_estimate": 0,
                    "shipping_estimate": 0,
                },
                status=status.HTTP_200_OK,
            )

        inventories = []
        # products = []
        # tiers = []
        total_cost = Decimal(0)
        total_compare_cost = Decimal(0)
        tax_estimate = Decimal(0)
        shipping_estimate = Decimal(0)
        # finalProductPrice = Decimal(0)
        # finalCoursePrice = Decimal(0)
        # finalTierPrice = Decimal(0)
        finalPrice = Decimal(0)

        for item in data.get("items"):
            if item.get("inventory"):
                inventories.append(item)
            # elif item.get("product"):
            #     products.append(item)
            # elif item.get("tier"):
            #     tiers.append(item)

        for object in inventories:
            inventory = object["inventory"] if object["inventory"] else None
            coupon = object["coupon"] if object["coupon"] else None

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
            if inventory_discount == False:
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

        finalPrice = Decimal(finalinventoryPrice)

        return self.send_response(
            {
                "total_cost": total_cost,
                "total_compare_cost": total_compare_cost,
                "finalPrice": finalPrice,
                "tax_estimate": tax_estimate,
                "shipping_estimate": shipping_estimate,
            },
            status=status.HTTP_200_OK,
        )


class AddItemToCartView(StandardAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data

        print("data", data)

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
            return self.send_error(
                "Item is already in cart", status=status.HTTP_409_CONFLICT
            )

        cart_item_object = CartItem.objects.create(
            inventory=inventory, cart=cart, quantity=quantity, coupon=coupon_id
        )

        if data.get("coupon").get("id") is not None:
            # Get the coupon object
            coupon = Coupon.objects.get(id=coupon_id)

            # Validate that the coupon applies to the inventory
            if coupon.inventory != inventory:
                return self.send_error(
                    "Coupon does not apply to this inventory",
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

        return self.send_response(
            {"cart": serialized_cart_items, "total_items": total_items},
            status=status.HTTP_200_OK,
        )


class RemoveItemView(StandardAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data

        item_id = data["itemID"]
        item_type = data["type"]
        cart, _ = Cart.objects.get_or_create(user=user)

        if item_type == "Inventory":
            inventory = Inventory.objects.get(id=item_id)
            cart_item = CartItem.objects.filter(cart=cart, inventory=inventory)

            if not cart_item.exists():
                return self.send_error(
                    "Item is not in cart", status=status.HTTP_404_NOT_FOUND
                )

            cart_item.delete()

            # Update the total number of items in the cart
            total_items = max(0, int(cart.total_items) - 1)
            Cart.objects.filter(user=user).update(total_items=total_items)

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return self.send_response(
            {"cart": serialized_cart_items, "total_items": total_items},
            status=status.HTTP_200_OK,
        )


class ClearCartView(StandardAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items.delete()
        cart.total_items = 0
        cart.save()
        serializer = CartSerializer(cart)
        return self.send_response(serializer.data, status=status.HTTP_200_OK)


class SynchCartItemsView(StandardAPIView):
    permission_classes = (permissions.IsAuthenticated,)

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
            if item["type"] == "Inventory":
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

        return self.send_response(
            {"cart": serialized_cart_items, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )
