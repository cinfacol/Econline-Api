from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
)  # Import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from inventory.models import Inventory

from .models import Cart, CartItem, DeliveryCost
from .serializers import CartSerializer, CartItemSerializer, DeliveryCostSerializer
from coupons.views import CheckCouponView  # Import CheckCouponView for validation logic


class GetItemsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)  # Ensure cart exists
        cartId = cart.id
        total_items = cart.total_items

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        # Get cart total including potential coupon discount
        cart_total = (
            cart.get_total()
        )  # get_total method in Cart model should handle coupon logic

        return Response(
            {
                "cartId": cartId,
                "cart_items": serialized_cart_items,
                "total_items": total_items,
                "cart_total": cart_total,  # Include the calculated total
                "coupon": CartSerializer(cart).data.get(
                    "coupon"
                ),  # Include coupon details if applied
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

        discount_amount = Decimal("0")
        coupon_data = None

        # Check if a coupon is applied to the cart and is valid
        if cart.coupon:
            coupon_checker = CheckCouponView()
            # Pass the subtotal to the validation logic
            validation_result = coupon_checker.validate_coupon(
                cart.coupon, user, subtotal
            )

            if validation_result["is_valid"]:
                discount_amount = coupon_checker.calculate_discount(
                    cart.coupon, subtotal
                )
                coupon_data = CouponSerializer(cart.coupon).data
            else:
                # If the coupon in the cart is no longer valid, remove it
                cart.coupon = None
                cart.save()

        final_total = subtotal - discount_amount
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
                "discount_amount": discount_amount,
                "final_total": final_total,
                "tax_estimate": tax_estimate,
                "shipping_estimate": shipping_estimate,
                "finalPrice": final_price_with_taxes_shipping,  # This seems to correspond to the final price including taxes/shipping in the original view
                "coupon": coupon_data,  # Include applied coupon data
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
        cart.coupon = None  # Remove applied coupon when clearing cart
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
                cart.coupon = None  # Remove applied coupon when clearing cart
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
            cart.coupon = None
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
        coupon_code = data.get("coupon_code")

        if not coupon_code:
            return Response(
                {"error": "Se requiere el código del cupón"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Cupón no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.all()  # Get cart items

        # Use the validation logic from coupons.views.CheckCouponView
        # Instantiate the view to access its methods
        coupon_checker = CheckCouponView()
        # Need to pass cart total and cart items to validate_coupon
        cart_total = (
            cart.get_total()
        )  # Assuming get_total calculates subtotal before coupon
        validation_result = coupon_checker.validate_coupon(
            coupon, user, cart_total, cart_items=cart_items
        )  # Pass cart_items

        if not validation_result["is_valid"]:
            return Response(
                {"error": validation_result["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply the coupon to the cart
        cart.coupon = coupon
        cart.save()

        # Recalculate total with the applied coupon and return updated cart details
        # The get_total method in the Cart model should now handle the coupon discount
        serialized_cart = CartSerializer(cart).data

        return Response(
            {"message": "Cupón aplicado exitosamente", "cart": serialized_cart},
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
            Cart.objects.filter(user=user).update(total_items=F("total_items") + 1)
            cart.refresh_from_db()  # Fetch the updated total_items value

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {"cart": serialized_cart_items, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class RemoveItemView(APIView):

    def post(self, request, format=None):
        user = request.user
        item_id = request.data

        if item_id is None:
            return Response(
                {"error": "Item ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        cart, _ = Cart.objects.get_or_create(user=user)
        inventory = get_object_or_404(Inventory, id=item_id)
        cart_item = CartItem.objects.filter(cart=cart, inventory=inventory).first()

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        # Update the total number of items in the cart
        total_items = max(0, int(cart.total_items) - 1)
        cart.total_items = total_items
        cart.save()
        # Cart.objects.filter(user=user).update(total_items=total_items)

        cart_items = CartItem.objects.filter(cart=cart)
        serialized_cart_items = CartItemSerializer(cart_items, many=True).data

        return Response(
            {"cart": serialized_cart_items, "total_items": total_items},
            status=status.HTTP_200_OK,
        )


class ClearCartView(APIView):

    def post(self, request, format=None):
        user = request.user
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items.delete()
        cart.total_items = 0
        cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DecreaseQuantityView(APIView):

    def put(self, request):
        user = request.user
        inventory_id = request.data
        item_id = inventory_id["inventoryId"]

        # Obtener o crear el carrito del usuario
        cart = Cart.objects.get(user=user)
        inventory = Inventory.objects.get(id=item_id)
        cart_item = CartItem.objects.get(cart=cart, inventory=inventory)
        quantity = cart_item.quantity

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        if quantity <= 1:
            return Response(
                {"message": "Proceed to remove the Product"},
                status=status.HTTP_200_OK,
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Limpiar el item existente
            cart_item.delete()

            # Update the total number of items in the cart
            quantity = max(0, int(cart_item.quantity) - 1)

            # Crear y guardar el ítem del carrito
            cart_item_quantity = CartItem(
                cart=cart, inventory=inventory, quantity=quantity
            )
            cart_item_quantity.save()

        return Response(
            {"quantity": cart_item.quantity},
            status=status.HTTP_200_OK,
        )


class IncreaseQuantityView(APIView):

    def put(self, request):
        user = request.user
        inventory_id = request.data
        item_id = inventory_id["inventoryId"]

        # Obtener o crear el carrito del usuario
        cart = Cart.objects.get(user=user)
        inventory = Inventory.objects.get(id=item_id)
        cart_item = CartItem.objects.get(cart=cart, inventory=inventory)
        quantity = cart_item.quantity

        if not cart_item:
            return Response(
                {"error": "Item is not in cart"}, status=status.HTTP_404_NOT_FOUND
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Limpiar el item existente
            cart_item.delete()

            # Update the total number of items in the cart
            quantity = max(0, int(cart_item.quantity) + 1)

            # Crear y guardar el ítem del carrito
            cart_item_quantity = CartItem(
                cart=cart, inventory=inventory, quantity=quantity
            )
            cart_item_quantity.save()

        return Response(
            {"quantity": cart_item.quantity},
            status=status.HTTP_200_OK,
        )


class SynchCartItemsView(APIView):

    def put(self, request):
        user = request.user
        data = request.data
        items = []

        # Obtener o crear el carrito del usuario
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = data.get("cart_items", [])

        # Si no hay ítems en el carrito, devolver error
        if not cart_items:
            return Response(
                {"error": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Utilizar una transacción atómica para garantizar la coherencia de los datos
        with transaction.atomic():
            # Limpiar los ítems existentes del carrito
            cart.cartitem_set.all().delete()

            # Recorrer los ítems del carrito
            for item_data in cart_items:
                inventory_id = item_data["inventory"]["id"]
                quantity = item_data.get("quantity", 1)

                # Validar si el inventario existe
                try:
                    inventory = Inventory.objects.get(id=inventory_id)
                except Inventory.DoesNotExist:
                    return Response(
                        {"error": f"Inventory with id {inventory_id} does not exist"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Crear y guardar el ítem del carrito (sin cupón)
                cart_item = CartItem(cart=cart, inventory=inventory, quantity=quantity)
                cart_item.save()
                items.append(cart_item)

            # Calcular el total de ítems en el carrito
            cart.total_items = len(items)
            cart.save()

        # Serializar los ítems del carrito y devolver la respuesta
        serialized_cart_items = CartItemSerializer(items, many=True).data
        return Response(
            {"cart": serialized_cart_items, "total_items": cart.total_items},
            status=status.HTTP_200_OK,
        )


class DeliveryCostListAPIView(APIView):
    """
    API endpoint for listing and creating delivery costs.
    """

    def get(self):
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

    def get(self, pk):
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

    def delete(self, pk):
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
        coupon_code = data.get("coupon_code")

        if not coupon_code:
            return Response(
                {"error": "Se requiere el código del cupón"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Cupón no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart, _ = Cart.objects.get_or_create(user=user)

        # Use the validation logic from coupons.views.CheckCouponView
        # Instantiate the view to access its methods
        coupon_checker = CheckCouponView()
        # Need to pass cart total to validate_coupon
        cart_total = (
            cart.get_total()
        )  # Assuming get_total calculates subtotal before coupon
        validation_result = coupon_checker.validate_coupon(coupon, user, cart_total)

        if not validation_result["is_valid"]:
            return Response(
                {"error": validation_result["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply the coupon to the cart
        cart.coupon = coupon
        cart.save()

        # Recalculate total with the applied coupon (logic needs to be added to Cart model's get_total or here)
        # For now, just return the updated cart details
        serialized_cart = CartSerializer(cart).data

        return Response(
            {"message": "Cupón aplicado exitosamente", "cart": serialized_cart},
            status=status.HTTP_200_OK,
        )
