from rest_framework import permissions
from .serializers import (
    CategorySerializer,
    InventorySerializer,
    ProductSerializer,
)
from .models import Category, Product, Inventory
from rest_framework.response import Response
from rest_framework.views import APIView


class CategoryList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)


class ProductByCategory(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, query=None):
        queryset = Product.objects.filter(category__slug=query)
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        queryset = (
            Inventory.objects.all()
            .values(
                "id",
                "pkid",
                "sku",
                "upc",
                "product__name",
                "product_id",
                "user__username",
                "order",
                "brand",
                "brand_id",
                "type__name",
                "type_id",
                "attribute_values",
                "is_active",
                "is_default",
                "published_status",
                "retail_price",
                "store_price",
                "is_digital",
                "weight",
                "views",
                "inventory_stock",
                "updated_at",
                "created_at",
                "inventory_media",
            )
            .order_by("-created_at")
        )
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryByRefCode(APIView):
    permission_classes = (permissions.AllowAny,)
    """
    Return Sub Product by RefCode
    """

    def get(self, request, query=None):
        queryset = Inventory.objects.filter(product__ref_code=query).values()
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
