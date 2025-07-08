from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from inventory.models import Inventory

from .models import Cart, CartItem, DeliveryCost
from .serializers import CartSerializer, CartItemSerializer, DeliveryCostSerializer
from coupons.views import (
    CheckCouponView,
    calculate_total_coupon_discount,
)  # Import CheckCouponView and the new utility function


class GetItemsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)  # Ensure cart exists
        cartId = cart.id
        total_items = cart.total_items

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        # Get cart total including potential coupon discount using the utility function
        subtotal = cart.get_total()  # get_total now calculates only subtotal
        total_discount = calculate_total_coupon_discount(cart, user)
        cart_total = subtotal - total_discount
        cart_total = max(Decimal("0"), cart_total)  # Ensure total is not negative

        return Response(
            {
                "cartId": cartId,
                "cart_items": serialized_cart_items,
                "total_items": total_items,
                "cart_total": cart_total,  # Include the calculated total
                "subtotal": subtotal,  # Include subtotal
                "discount_amount": total_discount,  # Include total discount
                "coupons": [
                    CouponSerializer(coupon).data for coupon in cart.coupons.all()
                ],  # Include coupon details if applied
            },
            status=status.HTTP_200_OK,
        )


class GetTotalView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def post(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)  # Ensure cart exists

        # The request data for this view seems to be a list of items,
        # which might be used for a temporary calculation without affecting the saved cart.
        # However, to reflect the applied coupon, we should use the user's actual cart items.
        # If the frontend sends item data for a different purpose (e.g., calculating total for selected items),
        # this logic might need adjustment. Assuming for now it's to get the total of the user's current cart.

        cart_items = cart.items.all()
        subtotal = Decimal("0")
        for item in cart_items:
            subtotal += Decimal(str(item.inventory.store_price)) * Decimal(
                str(item.quantity)
            )

        # Calculate total discount using the utility function
        total_discount = calculate_total_coupon_discount(cart, user)

        final_total = subtotal - total_discount
        # Ensure final total is not negative
        final_total = max(Decimal("0"), final_total)

        # Taxes and shipping estimates would need to be calculated based on the final_total and potentially other factors
        # For now, returning a simplified response including subtotal, discount, and final total.
        # The original GetTotalView logic for taxes and shipping was based on request data,
        # which might need to be adapted if the calculation should be based on the user's actual cart.

        # Placeholder for tax and shipping calculation based on final_total
        tax_estimate = Decimal("0")  # Replace with actual tax calculation
        shipping_estimate = Decimal("0")  # Replace with actual shipping calculation

        final_price_with_taxes_shipping = final_total + tax_estimate + shipping_estimate

        return Response(
            {
                "subtotal": subtotal,
                "discount_amount": total_discount,  # Use total_discount from utility function
                "final_total": final_total,
                "tax_estimate": tax_estimate,
                "shipping_estimate": shipping_estimate,
                "finalPrice": final_price_with_taxes_shipping,
                "coupons": [
                    CouponSerializer(coupon).data for coupon in cart.coupons.all()
                ],  # Include applied coupon data as a list
            },
            status=status.HTTP_200_OK,
        )


class AddItemToCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data

        item_id = data["inventory_id"]
        quantity = data["quantity"]

        try:
            inventory = Inventory.objects.get(id=item_id)
            stock = (
                inventory.inventory_stock.units - inventory.inventory_stock.units_sold
            )

        except Inventory.DoesNotExist:
            return Response(
                {"error": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND
            )

        cart, _ = Cart.objects.get_or_create(user=user)

        # Check if item already in cart
        if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
            return Response(
                {"error": "Item is already in cart"}, status=status.HTTP_409_CONFLICT
            )

        if int(stock) <= 0:
            return Response(
                {"error": "This product is out of stock"},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            cart_item = CartItem.objects.create(
                inventory=inventory, cart=cart, quantity=quantity
            )
            # Update total_items in the cart
            # Note: total_items should probably be the count of unique items, not total quantity
            # Cart.objects.filter(user=user).update(total_items=F("total_items") + 1)
            cart.total_items = cart.items.count()  # Recalculate based on items count
            cart.save()
            # cart.refresh_from_db()  # Fetch the updated total_items value - not needed if recalculating

        # Return the updated cart details including the coupon
        serialized_cart = CartSerializer(cart).data

        return Response(
            {"cart": serialized_cart, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class RemoveItemView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def post(self, request, format=None):
        user = request.user
        item_id = request.data.get(
            "inventory_id"
        )  # Assuming item_id is sent in request body
        if item_id is None:
            return Response(
                {"error": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(user=user)
        # Use filter().first() to avoid exception if item not found
        cart_item = CartItem.objects.filter(cart=cart, inventory__id=item_id).first()

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            cart_item.delete()
            # Update the total number of items in the cart
            cart.total_items = cart.items.count()  # Recalculate based on items count
            cart.save()

        # Return the updated cart details including the coupon
        serialized_cart = CartSerializer(cart).data

        return Response(
            {"cart": serialized_cart, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class ClearCartView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def post(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items.delete()
        cart.total_items = 0
        cart.coupons.clear()  # Remove all applied coupons when clearing cart
        cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DecreaseQuantityView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def put(self, request):
        user = request.user
        inventory_id_data = request.data
        item_id = inventory_id_data.get("inventoryId")  # Use .get() for safer access

        if not item_id:
            return Response(
                {"error": "Inventory ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener o crear el carrito del usuario
        cart, _ = Cart.objects.get_or_create(user=user)
        # Use filter().first() to avoid exception if item not found
        cart_item = CartItem.objects.filter(cart=cart, inventory__id=item_id).first()

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        quantity = cart_item.quantity

        if quantity <= 1:
            # If quantity is 1 or less, remove the item instead of decreasing quantity
            with transaction.atomic():
                cart_item.delete()
                cart.total_items = (
                    cart.items.count()
                )  # Recalculate based on items count
                cart.save()
            # Return the updated cart details including the coupon
            serialized_cart = CartSerializer(cart).data
            return Response(
                {
                    "message": "Product removed from cart",
                    "cart": serialized_cart,
                    "total_items": cart.total_items,
                },
                status=status.HTTP_200_OK,
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Decrease the quantity
            cart_item.quantity = quantity - 1
            cart_item.save()
            # total_items does not change when decreasing quantity of an existing item

        # Return the updated cart item quantity and potentially the updated cart total
        # To get the updated cart total, we would need to call cart.get_total() and include it in the response
        # For simplicity, returning just the updated quantity for now as per original view structure
        # If frontend needs updated total, modify this response and potentially the GetItemsView response structure
        return Response(
            {"quantity": cart_item.quantity},
            status=status.HTTP_200_OK,
        )


class IncreaseQuantityView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def put(self, request):
        user = request.user
        inventory_id_data = request.data
        item_id = inventory_id_data.get("inventoryId")  # Use .get() for safer access

        if not item_id:
            return Response(
                {"error": "Inventory ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener o crear el carrito del usuario
        cart, _ = Cart.objects.get_or_create(user=user)
        # Use filter().first() to avoid exception if item not found
        cart_item = CartItem.objects.filter(cart=cart, inventory__id=item_id).first()

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check for stock availability before increasing quantity
        inventory = cart_item.inventory
        available_stock = (
            inventory.inventory_stock.units - inventory.inventory_stock.units_sold
        )
        if cart_item.quantity + 1 > available_stock:
            return Response(
                {"error": "Not enough stock available"}, status=status.HTTP_409_CONFLICT
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Increase the quantity
            cart_item.quantity = cart_item.quantity + 1
            cart_item.save()
            # total_items does not change when increasing quantity of an existing item

        # Return the updated cart item quantity and potentially the updated cart total
        # To get the updated cart total, we would need to call cart.get_total() and include it in the response
        # For simplicity, returning just the updated quantity for now as per original view structure
        # If frontend needs updated total, modify this response and potentially the GetItemsView response structure
        return Response(
            {"quantity": cart_item.quantity},
            status=status.HTTP_200_OK,
        )


class SynchCartItemsView(APIView):
    permission_classes = (
        IsAuthenticated,
    )  # Assuming this view requires authentication

    def put(self, request):
        user = request.user
        data = request.data
        items_data = data.get("cart_items", [])

        # Obtener o crear el carrito del usuario
        cart, _ = Cart.objects.get_or_create(user=user)

        # If no items in the request, clear the cart
        if not items_data:
            with transaction.atomic():
                cart.cartitem_set.all().delete()
                cart.total_items = 0
                cart.coupons.clear()  # Remove applied coupons when clearing cart
                cart.save()
            serialized_cart = CartSerializer(cart).data
            return Response(
                {"cart": serialized_cart, "total_items": cart.total_items},
                status=status.HTTP_200_OK,
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Clear existing items from the cart
            cart.cartitem_set.all().delete()
            # Remove applied coupon when syncing items, as the total will be recalculated
            cart.coupons.clear()  # Remove applied coupons when syncing cart
            cart.save()

            created_items = []
            # Iterate over the cart items provided in the request
            for item_data in items_data:
                inventory_data = item_data.get("inventory")
                quantity = item_data.get("quantity", 1)

                if not inventory_data or "id" not in inventory_data:
                    # Skip items with missing inventory data or ID
                    continue

                inventory_id = inventory_data["id"]

                # Validate if the inventory exists
                try:
                    inventory = Inventory.objects.get(id=inventory_id)
                except Inventory.DoesNotExist:
                    # Optionally, return an error or skip the item
                    # For now, skipping the item and continuing
                    continue

                # Create and save the cart item
                cart_item = CartItem(cart=cart, inventory=inventory, quantity=quantity)
                cart_item.save()
                created_items.append(cart_item)

            # Calculate the total number of unique items in the cart
            cart.total_items = cart.items.count()
            cart.save()

        # Serialize the cart items and return the response
        # Return the full cart details including the coupon (which is now None)
        serialized_cart = CartSerializer(cart).data
        return Response(
            {"cart": serialized_cart, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class DeliveryCostListAPIView(APIView):
    """
    API endpoint for listing and creating delivery costs.
    """

    permission_classes = [IsAdminUser]  # Assuming admin permission is required

    def get(self, request):  # Add request parameter
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

    permission_classes = [IsAdminUser]  # Assuming admin permission is required

    def get_object(self, pk):
        try:
            return DeliveryCost.objects.get(pk=pk)
        except DeliveryCost.DoesNotExist:
            return None

    def get(self, request, pk):  # Add request parameter
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

    def delete(self, request, pk):  # Add request parameter
        delivery_cost = self.get_object(pk)
        if not delivery_cost:
            return Response(status=status.HTTP_404_NOT_FOUND)
        delivery_cost.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplyCouponView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data
        coupon_codes = data.get("coupon_codes", [])  # Expect a list of codes

        if not coupon_codes:
            return Response(
                {"error": "Se requiere al menos un código de cupón"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.all()  # Get cart items
        cart_subtotal = cart.get_total()  # get_total now calculates only subtotal

        applied_coupons = []
        errors = {}
        coupon_checker = CheckCouponView()

        # Clear existing coupons before applying new ones, or implement logic for adding/removing
        # For simplicity now, replacing existing coupons with the new list
        cart.coupons.clear()

        for code in coupon_codes:
            try:
                coupon = Coupon.objects.get(code=code)

                # Validate the coupon
                validation_result = coupon_checker.validate_coupon(
                    coupon, user, cart_subtotal, cart_items=cart_items
                )

                if validation_result["is_valid"]:
                    # Check for combinability if multiple coupons are being applied
                    if len(applied_coupons) > 0 and not coupon.can_combine:
                        errors[code] = (
                            "Este cupón no se puede combinar con otros cupones."
                        )
                        continue  # Skip applying this coupon

                    # Check if any already applied coupon is not combinable
                    if any(not c.can_combine for c in applied_coupons):
                        errors[code] = (
                            "No se puede aplicar este cupón con los cupones existentes."
                        )
                        continue  # Skip applying this coupon

                    applied_coupons.append(coupon)
                    cart.coupons.add(coupon)  # Associate coupon with the cart

                else:
                    errors[code] = validation_result[
                        "message"
                    ]  # Store validation error

            except Coupon.DoesNotExist:
                errors[code] = "Cupón no encontrado"  # Store not found error

        cart.save()  # Save the cart with associated coupons

        # Recalculate total with the applied coupons and return updated cart details
        # Use the utility function to get the total discount
        total_discount = calculate_total_coupon_discount(cart, user)
        subtotal = cart.get_total()  # get_total now calculates only subtotal
        final_total = subtotal - total_discount
        final_total = max(Decimal("0"), final_total)  # Ensure total is not negative

        serialized_cart = CartSerializer(cart).data

        response_data = {
            "message": "Procesamiento de cupones completado",
            "cart": serialized_cart,
            "subtotal": subtotal,
            "discount_amount": total_discount,
            "final_total": final_total,
        }
        if errors:
            response_data["errors"] = errors  # Include errors in the response

        status_code = status.HTTP_200_OK if not errors else status.HTTP_400_BAD_REQUEST

        return Response(
            response_data,
            status=status_code,
        )
