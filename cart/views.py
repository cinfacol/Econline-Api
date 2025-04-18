from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import JSONParser
from decimal import Decimal


from .models import Cart, CartItem, DeliveryCost
from coupons.models import Coupon
from .serializers import CartSerializer, CartItemSerializer, DeliveryCostSerializer
from inventory.models import Inventory
from inventory.serializers import InventorySerializer
from django.shortcuts import get_object_or_404


class GetItemsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        cart = Cart.objects.get(user=user)
        cartId = cart.id
        total_items = cart.total_items

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

    def post(self, request, format=None):
        original_data = JSONParser().parse(request)
        data = {"items": original_data}

        # Check for missing data and return error if necessary
        if not data or not data.get("items"):
            return Response(
                {
                    "total_cost": 0,
                    "total_compare_cost": 0,
                    "finalPrice": 0,
                    "tax_estimate": 0,
                    "shipping_estimate": 0,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventories = []
        total_cost = Decimal(0)
        total_compare_cost = Decimal(0)
        tax_estimate = Decimal(0)
        final_inventory_retail_price = Decimal(0)
        shipping_estimate = Decimal(0)
        quantity = Decimal(0)

        for item in data.get("items", []):
            if item.get("inventory"):
                inventories.append(item)

        for object in inventories:
            inventory = object.get("inventory", {})  # Use default empty dict if missing
            coupon = object.get("coupon", None)

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

            inventory_retail_price = inventory.get("retail_price")
            inventory_compare_price = inventory.get(
                "store_price", inventory_retail_price
            )
            inventory_discount = inventory.get("promotion_price", False)
            taxes = inventory.get("taxe")

            # Calculate Total Cost Without Discounts and Coupons and Taxes (total_cost)
            if inventory_discount == False:
                total_cost += Decimal(inventory_retail_price)
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
                        Decimal(inventory_retail_price)
                        - Decimal(coupon_fixed_discount_price),
                        0,
                    )
                elif coupon_discount_percentage is not None:
                    total_compare_cost += Decimal(inventory_retail_price) * (
                        1 - (Decimal(coupon_discount_percentage) / 100)
                    )
                else:
                    total_compare_cost += Decimal(inventory_retail_price)

        # Calculate Taxes for Total Cost (tax_estimate)
        tax_estimate = Decimal(inventory_retail_price) * Decimal(taxes)

        final_inventory_retail_price = Decimal(inventory_retail_price) + Decimal(
            tax_estimate
        )

        return Response(
            {
                "total_cost": total_cost,
                "total_compare_cost": total_compare_cost,
                "finalPrice": final_inventory_retail_price,
                "tax_estimate": tax_estimate,
                "shipping_estimate": shipping_estimate,  # Include shipping estimate if available
            },
            status=status.HTTP_200_OK,
        )


class AddItemToCartView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        data = request.data

        item_id = data["inventory_id"]
        coupon_id = data.get("coupon", {}).get("id")
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

            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    if coupon.inventory != inventory:
                        return Response(
                            {"error": "Coupon does not apply to this inventory"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    cart_item.coupon = coupon
                    cart_item.save()
                except Coupon.DoesNotExist:
                    return Response(
                        {"error": "Invalid coupon"}, status=status.HTTP_400_BAD_REQUEST
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

    def put(self, request, format=None):
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

    def put(self, request, format=None):
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

    def put(self, request, format=None):
        user = request.user
        data = request.data
        items = []
        inventories = []

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

                # Manejo seguro del cupón
                coupon_data = item_data.get("coupon")
                # print("coupon_data:", coupon_data)
                coupon = None
                if isinstance(coupon_data, dict):
                    coupon_id = coupon_data.get("id")
                else:
                    coupon_id = (
                        None  # Si es una cadena o no es válido, lo dejamos como None
                    )

                # Obtener el cupón si se proporciona el id

                if coupon_id:
                    try:
                        coupon = Coupon.objects.get(id=coupon_id)
                    except Coupon.DoesNotExist:
                        return Response(
                            {"error": f"Coupon with id {coupon_id} does not exist"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                # Crear y guardar el ítem del carrito
                cart_item = CartItem(
                    cart=cart, inventory=inventory, coupon=coupon, quantity=quantity
                )
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
