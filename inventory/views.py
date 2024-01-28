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
    """
    Return list of all categories
    """

    def get(self, request):
        queryset = Category.objects.all().values()
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)


class ProductByCategory(APIView):
    permission_classes = (permissions.AllowAny,)
    """
    Return product by category
    """

    def get(self, request, query=None):
        queryset = Product.objects.filter(category__name=query).values()
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryList(APIView):
    permission_classes = (permissions.AllowAny,)
    """
    Return list of all categories
    """

    def get(self, request):
        queryset = Inventory.objects.all().values()
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
