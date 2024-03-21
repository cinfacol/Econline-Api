from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem

from inventory.models import Inventory
from inventory.serializers import InventorySerializer


class GetItemsView(APIView):
    def get(self, request, format=None):
        user = self.request.user
        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.order_by("inventory").filter(cart=cart)

            result = []

            if CartItem.objects.filter(cart=cart).exists():
                for cart_item in cart_items:
                    item = {}

                    item["id"] = cart_item.id
                    item["count"] = cart_item.count
                    inventory = Inventory.objects.get(id=cart_item.inventory.id)
                    inventory = InventorySerializer(inventory)

                    item["inventory"] = inventory.data

                    result.append(item)
            return Response({"cart": result}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when retrieving cart items"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AddItemView(APIView):
    def post(self, request, format=None):
        user = self.request.user
        data = self.request.data

        try:
            inventory_id = str(data["inventory_id"])
        except:
            return Response(
                {"error": "Inventory ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        count = 1

        try:
            if not Inventory.objects.filter(id=inventory_id).exists():
                return Response(
                    {"error": "This inventory does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            inventory = Inventory.objects.get(id=inventory_id)

            cart = Cart.objects.get(user=user)

            if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                return Response(
                    {"error": "Item is already in cart"},
                    status=status.HTTP_409_CONFLICT,
                )

            if int(inventory.inventory_stock.units) > 0:
                CartItem.objects.create(inventory=inventory, cart=cart, count=count)

                if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                    total_items = int(cart.total_items) + 1
                    Cart.objects.filter(user=user).update(total_items=total_items)

                    cart_items = CartItem.objects.order_by("inventory").filter(
                        cart=cart
                    )

                    result = []

                    for cart_item in cart_items:

                        item = {}
                        item["id"] = cart_item.id
                        item["count"] = cart_item.count
                        inventory = Inventory.objects.get(id=cart_item.inventory.id)
                        inventory = InventorySerializer(inventory)

                        item["inventory"] = inventory.data

                        result.append(item)

                    return Response({"cart": result}, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {"error": "Not enough of this item in stock"},
                        status=status.HTTP_200_OK,
                    )
        except:
            return Response(
                {"error": "Something went wrong when adding item to cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetTotalView(APIView):
    def get(self, request, format=None):
        user = self.request.user

        try:
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)

            total_cost = 0.0
            total_compare_cost = 0.0

            if cart_items.exists():
                for cart_item in cart_items:
                    total_cost += float(cart_item.inventory.retail_price) * float(
                        cart_item.count
                    )
                    total_compare_cost += float(
                        cart_item.inventory.store_price
                    ) * float(cart_item.count)
                total_cost = round(total_cost, 2)
                total_compare_cost = round(total_compare_cost, 2)
            return Response(
                {"total_cost": total_cost, "total_compare_cost": total_compare_cost},
                status=status.HTTP_200_OK,
            )
        except:
            return Response(
                {"error": "Something went wrong when retrieving total costs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetItemTotalView(APIView):
    def get(self, request, format=None):
        user = self.request.user

        try:
            cart = Cart.objects.get(user=user)
            total_items = cart.total_items

            return Response({"total_items": total_items}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when getting total number of items"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateItemView(APIView):
    def put(self, request, format=None):
        user = self.request.user
        data = self.request.data
        # print("data", data)

        try:
            inventory_id = str(data["inventory_id"])
        except:
            return Response(
                {"error": "Inventory ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            count = int(data["count"])
        except:
            return Response(
                {"error": "Count value must be an integer"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not Inventory.objects.filter(id=inventory_id).exists():
                return Response(
                    {"error": "This inventory does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            inventory = Inventory.objects.get(id=inventory_id)
            cart = Cart.objects.get(user=user)

            if not CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                return Response(
                    {"error": "This inventory is not in your cart"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            quantity = inventory.inventory_stock.units

            if count <= quantity:
                CartItem.objects.filter(inventory=inventory, cart=cart).update(
                    count=count
                )

                cart_items = CartItem.objects.order_by("inventory").filter(cart=cart)

                result = []

                for cart_item in cart_items:
                    item = {}

                    item["id"] = cart_item.id
                    item["count"] = cart_item.count
                    inventory = Inventory.objects.get(id=cart_item.inventory.id)
                    inventory = InventorySerializer(inventory)

                    item["inventory"] = inventory.data

                    result.append(item)

                return Response({"cart": result}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Not enough of this item in stock"},
                    status=status.HTTP_200_OK,
                )
        except:
            return Response(
                {"error": "Something went wrong when updating cart item"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RemoveItemView(APIView):
    def delete(self, request, format=None):
        user = self.request.user
        data = self.request.data

        try:
            inventory_id = str(data["inventory_id"])
        except:
            return Response(
                {"error": "Inventory ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not Inventory.objects.filter(id=inventory_id).exists():
                return Response(
                    {"error": "This inventory does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            inventory = Inventory.objects.get(id=inventory_id)
            cart = Cart.objects.get(user=user)

            if not CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                return Response(
                    {"error": "This inventory is not in your cart"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            CartItem.objects.filter(cart=cart, inventory=inventory).delete()

            if not CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                # actualizar numero total en el carrito
                total_items = int(cart.total_items) - 1
                Cart.objects.filter(user=user).update(total_items=total_items)

            cart_items = CartItem.objects.order_by("inventory").filter(cart=cart)

            result = []

            if CartItem.objects.filter(cart=cart).exists():
                for cart_item in cart_items:
                    item = {}

                    item["id"] = cart_item.id
                    item["count"] = cart_item.count
                    inventory = Inventory.objects.get(id=cart_item.inventory.id)
                    inventory = InventorySerializer(inventory)

                    item["inventory"] = inventory.data

                    result.append(item)

            return Response({"cart": result}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when removing item"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmptyCartView(APIView):
    def delete(self, request, format=None):
        user = self.request.user

        try:
            cart = Cart.objects.get(user=user)

            if not CartItem.objects.filter(cart=cart).exists():
                return Response(
                    {"success": "Cart is already empty"}, status=status.HTTP_200_OK
                )

            CartItem.objects.filter(cart=cart).delete()

            # Actualizamos carrito
            Cart.objects.filter(user=user).update(total_items=0)

            return Response(
                {"success": "Cart emptied successfully"}, status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "Something went wrong emptying cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SynchCartView(APIView):
    def put(self, request, format=None):
        user = self.request.user
        data = self.request.data
        print("data", data)

        try:
            cart_items = data["cart_items"]
            print("cart_items", cart_items)

            for cart_item in cart_items:
                cart = Cart.objects.get(user=user)

                try:
                    inventory_id = str(cart_item["inventory_id"])
                except:
                    return Response(
                        {"error": "Inventory ID must be an string"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if not Inventory.objects.filter(id=inventory_id).exists():
                    return Response(
                        {"error": "Inventory with this ID does not exist"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                inventory = Inventory.objects.get(id=inventory_id)
                quantity = inventory.inventory_stock.units

                if CartItem.objects.filter(cart=cart, inventory=inventory).exists():
                    # Actualiizamos el item del carrito
                    item = CartItem.objects.get(cart=cart, inventory=inventory)
                    count = item.count

                    try:
                        cart_item_count = int(cart_item["count"])
                    except:
                        cart_item_count = 1

                    # Chqueo con base de datos
                    if (cart_item_count + int(count)) <= int(quantity):
                        updated_count = cart_item_count + int(count)
                        CartItem.objects.filter(cart=cart, inventory=inventory).update(
                            count=updated_count
                        )
                else:
                    # Agregar el item al carrito del usuario
                    try:
                        cart_item_count = int(cart_item["count"])
                    except:
                        cart_item_count = 1

                    if cart_item_count <= quantity:
                        CartItem.objects.create(
                            inventory=inventory, cart=cart, count=cart_item_count
                        )

                        if CartItem.objects.filter(
                            cart=cart, inventory=inventory
                        ).exists():
                            # Sumar item
                            total_items = int(cart.total_items) + 1
                            Cart.objects.filter(user=user).update(
                                total_items=total_items
                            )

                return Response(
                    {"success": "Cart Synchronized"}, status=status.HTTP_201_CREATED
                )
        except:
            return Response(
                {"error": "Something went wrong when synching cart"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
