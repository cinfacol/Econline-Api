from django.shortcuts import render
from .serializers import (
    CategorySerializer,
    InventorySerializer,
    ProductSerializer,
)
from .models import Category, Product, Inventory
from rest_framework.response import Response
from rest_framework.views import APIView


class CategoryList(APIView):
    """
    Return list of all categories
    """

    def get(self, request):
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)


class ProductByCategory(APIView):
    """
    Return product by category
    """

    def get(self, request, query=None):
        queryset = Product.objects.filter(category__slug=query)
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryByUpc(APIView):
    """
    Return Sub Product by Upc
    """

    def get(self, request, query=None):
        queryset = Inventory.objects.filter(product__upc=query)
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
