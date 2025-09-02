from .models import Brand
from .serializers import BrandSerializer


import django_filters
from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Inventory, InventoryViews, Media
from .exceptions import InventoryNotFound
from .pagination import InventoryPagination
from .serializers import (
    InventorySerializer,
    InventoryViewSerializer,
    InventoryCreateSerializer,
    InventoryImagesSerializer,
)


# Vista para listar marcas
class BrandListAPIView(generics.ListAPIView):
    queryset = Brand.objects.all().order_by("name")
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]


# Vista para crear marcas
class BrandCreateAPIView(generics.CreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAdminUser]


class InventoryFilter(django_filters.FilterSet):

    type__slug = django_filters.CharFilter(lookup_expr="icontains")
    quality = django_filters.CharFilter(field_name="quality", lookup_expr="iexact")
    retail_price = django_filters.NumberFilter()
    retail_price__gt = django_filters.NumberFilter(
        field_name="retail_price", lookup_expr="gt"
    )
    retail_price__lt = django_filters.NumberFilter(
        field_name="retail_price", lookup_expr="lt"
    )

    class Meta:
        model = Inventory
        fields = ["type", "quality", "retail_price"]


class InventoryListAPIView(generics.ListAPIView):
    serializer_class = InventorySerializer
    queryset = Inventory.objects.all().order_by("-created_at")
    permission_classes = [permissions.AllowAny]
    pagination_class = InventoryPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = InventoryFilter
    search_fields = ["product", "type"]
    ordering_fields = ["created_at"]


class ListUsersInventoryAPIView(generics.ListAPIView):

    serializer_class = InventorySerializer
    pagination_class = InventoryPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = InventoryFilter
    search_fields = ["product", "type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Inventory.objects.filter(user=user).order_by("-created_at")
        return queryset


class InventoryViewsAPIView(generics.ListAPIView):
    serializer_class = InventoryViewSerializer
    queryset = InventoryViews.objects.all()


class InventoryDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        inventory = Inventory.objects.get(id=id)

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        if not InventoryViews.objects.filter(inventory=inventory, ip=ip).exists():
            InventoryViews.objects.create(inventory=inventory, ip=ip)

            inventory.views += 1
            inventory.save()

        serializer = InventorySerializer(inventory, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryByCategoryAPIView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    pagination_class = InventoryPagination
    serializer_class = InventorySerializer
    queryset = Inventory.objects.all()

    def get_queryset(self):
        categories_string = self.kwargs.get(
            "query", None
        )  # Get comma-separated categories
        if categories_string:
            categories = categories_string.split(
                ","
            )  # Split into individual categories
            self.queryset = self.queryset.filter(product__category__slug__in=categories)
        return self.queryset


class InventoryByRefCode(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, query=None):
        queryset = Inventory.objects.filter(product__ref_code=query)
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)


class InventoryImages(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        inventories = Inventory.objects.all()
        serializer = InventoryImagesSerializer(inventories, many=True)
        return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([permissions.IsAdminUser])
def update_inventory_api_view(request, sku):
    try:
        inventory = Inventory.objects.get(sku=sku)
    except Inventory.DoesNotExist:
        raise InventoryNotFound

    user = request.user
    if inventory.user != user:
        return Response(
            {
                "error": _(
                    "You can't update or edit an inventory that doesn't belong to you"
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if request.method == "PUT":
        data = request.data
        serializer = InventorySerializer(inventory, data, many=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def create_inventory_api_view(request):
    data = request.data
    data["user"] = request.user.pkid
    serializer = InventoryCreateSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([permissions.IsAdminUser])
def delete_inventory_api_view(request, sku):
    try:
        inventory = Inventory.objects.get(sku=sku)
    except Inventory.DoesNotExist:
        raise InventoryNotFound

    user = request.user
    if inventory.user != user:
        return Response(
            {"error": _("You can't delete a inventory that doesn't belong to you")},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "DELETE":
        delete_operation = inventory.delete()
        data = {}
        if delete_operation:
            data["success"] = "Deletion was successful"
        else:
            data["failure"] = "Deletion failed"
        return Response(data=data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def search_api_view(request):
    query = request.query_params.get("query")
    if query is None:
        query = ""
    inventory = Inventory.objects.filter(product__name__icontains=query)
    inventory = Inventory.objects.filter(product__description__icontains=query)
    serializer = InventorySerializer(inventory, many=True)
    return Response({"inventories": serializer.data})


class InventorySearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InventoryCreateSerializer

    def post(self, request):
        queryset = Inventory.objects.filter(published_status=True)
        data = self.request.data

        type = data["type"]
        queryset = queryset.filter(type__iexact=type)

        quality = data["quality"]
        queryset = queryset.filter(quality__iexact=quality)

        store_price = data["store_price"]
        if store_price == "$0+":
            store_price = 0
        elif store_price == "$50,000+":
            store_price = 50000
        elif store_price == "$100,000+":
            store_price = 100000
        elif store_price == "$200,000+":
            store_price = 200000
        elif store_price == "$400,000+":
            store_price = 400000
        elif store_price == "$600,000+":
            store_price = 600000
        elif store_price == "Any":
            store_price = -1

        if store_price != -1:
            queryset = queryset.filter(store_price__gte=store_price)

        catch_phrase = data["catch_phrase"]
        queryset = queryset.filter(description__icontains=catch_phrase)

        serializer = InventorySerializer(queryset, many=True)

        return Response(serializer.data)
