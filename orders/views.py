from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from django.utils import timezone
import datetime
import logging

logger = logging.getLogger(__name__)

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
        except Exception as e:
            logger.error(f"Error retrieving orders: {str(e)}")
            return Response(
                {"error": "Something went wrong when retrieving orders"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListOrderDetailView(APIView):
    def get(self, request, transactionId, format=None):
        user = self.request.user
        logger.info(f"Retrieving order details for transaction_id: {transactionId}")

        try:
            order = Order.objects.select_related("shipping", "address", "user").get(
                user=user, transaction_id=transactionId
            )

            result = {
                "status": order.status,
                "transaction_id": order.transaction_id,
                "amount": order.amount,
                "created_at": order.created_at,
            }

            # Agregar información de envío si existe
            if order.shipping:
                result.update(
                    {
                        "shipping_name": order.shipping.name,
                        "shipping_time": order.shipping.time_to_delivery,
                        "shipping_price": order.shipping.standard_shipping_cost,
                    }
                )

            # Agregar información de dirección si existe
            if order.address:
                address_data = {
                    "address_line_1": order.address.address_line_1,
                    "address_line_2": order.address.address_line_2 or "",
                    "city": order.address.city,
                    "state_province_region": order.address.state_province_region,
                    "postal_zip_code": order.address.postal_zip_code,
                    "country_region": order.address.country_region,
                }
                result.update(address_data)

            # Agregar información del usuario
            if order.user:
                result["full_name"] = f"{order.user.first_name} {order.user.last_name}"

            # Obtener items de la orden
            order_items = OrderItem.objects.filter(order=order)
            result["order_items"] = [
                {
                    "name": item.name,
                    "price": item.price,
                    "count": item.count,
                }
                for item in order_items
            ]

            return Response({"order": result}, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            logger.warning(f"Order not found for transaction_id: {transactionId}")
            return Response(
                {"error": "Order with this transaction ID does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error retrieving order detail: {str(e)}")
            return Response(
                {"error": "Something went wrong when retrieving order detail"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
