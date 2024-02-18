from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from profiles.models import Address


class ListOrdersView(APIView):
    def get(self, request, format=None):
        user = self.request.user
        try:
            orders = Order.objects.order_by("-date_issued").filter(user=user)
            result = []

            for order in orders:
                item = {}
                item["status"] = order.status
                item["transaction_id"] = order.transaction_id
                item["amount"] = order.amount
                item["shipping_price"] = order.shipping_price
                item["date_issued"] = order.date_issued
                item["address"] = order.order_address.address
                item["address_2"] = order.order_address.address_2

                result.append(item)

            return Response({"orders": result}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when retrieving orders"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListOrderDetailView(APIView):
    def get(self, request, transactionId, format=None):
        user = self.request.user

        try:
            if Order.objects.filter(user=user, transaction_id=transactionId).exists():
                order = Order.objects.get(user=user, transaction_id=transactionId)
                result = {}
                result["status"] = order.status
                result["transaction_id"] = order.transaction_id
                result["amount"] = order.amount
                result["full_name"] = order.full_name
                result["address_line_1"] = order.address_line_1
                result["address_line_2"] = order.address_line_2
                result["city"] = order.city
                result["state_province_region"] = order.state_province_region
                result["postal_zip_code"] = order.postal_zip_code
                result["country_region"] = order.country_region
                result["telephone_number"] = order.telephone_number
                result["shipping_name"] = order.shipping_name
                result["shipping_time"] = order.shipping_time
                result["shipping_price"] = order.shipping_price
                result["date_issued"] = order.date_issued

                order_items = OrderItem.objects.order_by("-date_added").filter(
                    order=order
                )
                result["order_items"] = []

                for order_item in order_items:
                    sub_item = {}

                    sub_item["name"] = order_item.name
                    sub_item["price"] = order_item.price
                    sub_item["count"] = order_item.count

                    result["order_items"].append(sub_item)
                return Response({"order": result}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Order with this transaction ID does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except:
            return Response(
                {"error": "Something went wrong when retrieving order detail"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


""" from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from .models import Order, Orderitem, ShippingAddress
from .serializers import OrderSerializer
from products.models import Product


@api_view(["GET"])
@permission_classes([IsAdminUser])
def search(request):
    query = request.query_params.get("query")
    if query is None:
        query = ""
    order = Order.objects.filter(user__email__icontains=query)
    serializer = OrderSerializer(order, many=True)
    return Response({"orders": serializer.data})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_orders(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    user = request.user
    data = request.data
    orderItems = data["order_items"]
    total_price = data["total_price"]

    sum_of_prices = sum(
        int(float(item["price"])) * item["quantity"] for item in orderItems
    )

    if total_price == sum_of_prices:
        order = Order.objects.create(user=user, total_price=total_price)

        ShippingAddress.objects.create(
            order=order,
            address=data["address"],
            city=data["city"],
            postal_code=data["postal_code"],
        )

        for i in orderItems:
            product = Product.objects.get(id=i["id"])
            item = Orderitem.objects.create(
                product=product, order=order, quantity=i["quantity"], price=i["price"]
            )

            product.count_in_stock -= item.quantity
            product.save()

        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response({"mensaje": sum_of_prices}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def solo_order(request, pk):
    user = request.user
    try:
        order = Order.objects.get(pk=pk)
        if user.is_staff or order.user == user:
            serializer = OrderSerializer(order, many=False)
            return Response(serializer.data)
        else:
            Response(
                {"detail": "No access to view orders"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    except:
        return Response(
            {"detail": "Order does not exist"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    user = request.user
    orders = user.order_set.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAdminUser])
def delivered(request, pk):
    order = Order.objects.get(pk=pk)
    order.is_delivered = True
    order.delivered_at = datetime.now()
    order.save()
    return Response("Order was delivered") """
