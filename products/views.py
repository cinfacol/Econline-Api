# import logging

import django_filters
from django.db.models import query
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ProductNotFound
from .models import Product

# from .models import Product, ProductViews
from .pagination import ProductPagination
from .serializers import (
    ProductSerializer,
)

# logger = logging.getLogger(__name__)


# class ProductFilter(django_filters.FilterSet):
#     # advert_type = django_filters.CharFilter(
#     #     field_name="advert_type", lookup_expr="iexact"
#     # )

#     product_type = django_filters.CharFilter(
#         field_name="product_type", lookup_expr="iexact"
#     )

#     price = django_filters.NumberFilter()
#     price__gt = django_filters.NumberFilter(field_name="price", lookup_expr="gt")
#     price__lt = django_filters.NumberFilter(field_name="price", lookup_expr="lt")

#     class Meta:
#         model = Product
#         fields = ["product_type", "price"]


# class ListAllProductsAPIView(generics.ListAPIView):
#     permission_classes = (permissions.AllowAny,)
#     serializer_class = ProductSerializer
#     queryset = Product.objects.all().order_by("-created_at")
#     pagination_class = ProductPagination
#     filter_backends = [
#         DjangoFilterBackend,
#         filters.SearchFilter,
#         filters.OrderingFilter,
#     ]

#     filterset_class = ProductFilter
#     search_fields = ["name"]
#     ordering_fields = ["created_at"]


""" class ProductSearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        queryset = Product.objects.filter(published_status=True)
        data = self.request.data

        advert_type = data["advert_type"]
        queryset = queryset.filter(advert_type__iexact=advert_type)

        product_type = data["product_type"]
        queryset = queryset.filter(product_type__iexact=product_type)

        price = data["price"]
        if price == "$0+":
            price = 0
        elif price == "$50,000+":
            price = 50000
        elif price == "$100,000+":
            price = 100000
        elif price == "$200,000+":
            price = 200000
        elif price == "$400,000+":
            price = 400000
        elif price == "$600,000+":
            price = 600000
        elif price == "Any":
            price = -1

        if price != -1:
            queryset = queryset.filter(price__gte=price)

        bedrooms = data["bedrooms"]
        if bedrooms == "0+":
            bedrooms = 0
        elif bedrooms == "1+":
            bedrooms = 1
        elif bedrooms == "2+":
            bedrooms = 2
        elif bedrooms == "3+":
            bedrooms = 3
        elif bedrooms == "4+":
            bedrooms = 4
        elif bedrooms == "5+":
            bedrooms = 5

        queryset = queryset.filter(bedrooms__gte=bedrooms)

        bathrooms = data["bathrooms"]
        if bathrooms == "0+":
            bathrooms = 0.0
        elif bathrooms == "1+":
            bathrooms = 1.0
        elif bathrooms == "2+":
            bathrooms = 2.0
        elif bathrooms == "3+":
            bathrooms = 3.0
        elif bathrooms == "4+":
            bathrooms = 4.0

        queryset = queryset.filter(bathrooms__gte=bathrooms)

        catch_phrase = data["catch_phrase"]
        queryset = queryset.filter(description__icontains=catch_phrase)

        serializer = ProductSerializer(queryset, many=True)

        return Response(serializer.data) """
