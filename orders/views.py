from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from django.utils import timezone
import datetime

# Convertir un datetime naive a aware
naive_datetime = datetime.datetime.now()
aware_datetime = timezone.make_aware(naive_datetime)


class ListOrdersView(APIView):
    def get(self, request, format=None):
        user = self.request.user

        try:
            orders = Order.objects.order_by("-created_at").filter(user=user)
            result = []

            for order in orders:
                item = {}
                item["status"] = order.status
                item["transaction_id"] = order.transaction_id
                item["amount"] = order.amount
                item["shipping_price"] = order.shipping_price
                item["created_at"] = order.created_at
                item["address_line_1"] = order.address_line_1
                item["address_line_2"] = order.address_line_2

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
                result["created_at"] = order.created_at

                order_items = OrderItem.objects.order_by("-created_at").filter(
                    order=order
                )
                result["order_items"] = []

                for order_item in order_items:
                    sub_item = {}

                    # sub_item["id"] = order_item.inventory.id
                    # sub_item["description"] = order_item.inventory.product.description
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
