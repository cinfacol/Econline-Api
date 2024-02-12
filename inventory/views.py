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


class InventoryByCategory(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, query=None):
        queryset = Inventory.objects.filter(product__category__slug=query)
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        queryset = Inventory.objects.all()
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryByRefCode(APIView):
    permission_classes = (permissions.AllowAny,)
    """
    Return Sub Product by RefCode
    """

    def get(self, request, query=None):
        queryset = Inventory.objects.filter(product__ref_code=query)
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
