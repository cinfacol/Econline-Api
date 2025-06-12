from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.utils import timezone
from django.db.models import Q

from .models import Coupon, Campaign, CouponUsage
from .serializers import CouponSerializer, CampaignSerializer, CouponUsageSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CheckCouponView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.query_params.get("code")
        name = request.query_params.get("name")
        user = request.user if request.user.is_authenticated else None
        cart_total = request.query_params.get("cart_total", 0)

        if not code and not name:
            return Response(
                {"error": "Se requiere un código o nombre de cupón"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Buscar por código o nombre
            if code:
                coupon = Coupon.objects.get(code=code)
            else:
                # Buscar por nombre de forma flexible
                coupon = Coupon.objects.filter(name__icontains=name).first()
                if not coupon:
                    return Response(
                        {"error": "Cupón no encontrado"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # Validar el cupón
            validation_result = self.validate_coupon(coupon, user, cart_total)
            if not validation_result["is_valid"]:
                return Response(
                    {"error": validation_result["message"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calcular el descuento
            discount = self.calculate_discount(coupon, cart_total)

            serialized_coupon = CouponSerializer(coupon).data
            return Response(
                {
                    "coupon": serialized_coupon,
                    "discount": discount,
                    "is_valid": True,
                },
                status=status.HTTP_200_OK,
            )

        except Coupon.DoesNotExist:
            return Response(
                {"error": "Cupón no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def validate_coupon(self, coupon, user, cart_total):
        now = timezone.now()

        # Validar fechas
        if not (coupon.start_date <= now <= coupon.end_date):
            return {"is_valid": False, "message": "El cupón no está vigente"}

        # Validar estado
        if not coupon.is_active:
            return {"is_valid": False, "message": "El cupón no está activo"}

        # Validar monto mínimo
        if coupon.min_purchase_amount and float(cart_total) < float(
            coupon.min_purchase_amount
        ):
            return {
                "is_valid": False,
                "message": f"El monto mínimo de compra es ${coupon.min_purchase_amount}",
            }

        # Validar usos totales
        if coupon.max_uses <= coupon.used_by.count():
            return {
                "is_valid": False,
                "message": "El cupón ha alcanzado su límite de usos",
            }

        # Validar usos por usuario
        if (
            user
            and coupon.max_uses_per_user <= coupon.used_by.filter(id=user.id).count()
        ):
            return {
                "is_valid": False,
                "message": "Has alcanzado el límite de usos para este cupón",
            }

        # Validar primera compra
        if coupon.first_purchase_only and user and user.orders.exists():
            return {
                "is_valid": False,
                "message": "Este cupón es solo para primera compra",
            }

        return {"is_valid": True, "message": "Cupón válido"}

    def calculate_discount(self, coupon, cart_total):
        cart_total = float(cart_total)

        if coupon.fixed_price_coupon:
            discount = float(coupon.fixed_price_coupon.discount_price)
        elif coupon.percentage_coupon:
            discount = cart_total * (coupon.percentage_coupon.discount_percentage / 100)
        else:
            return 0

        # Aplicar límite máximo de descuento si existe
        if coupon.max_discount_amount:
            discount = min(discount, float(coupon.max_discount_amount))

        return round(discount, 2)


class CouponListView(ListCreateAPIView):
    serializer_class = CouponSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Coupon.objects.all()

        # Filtros
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Búsqueda por nombre o código
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CouponDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "pk"


class CouponUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            coupon = Coupon.objects.get(pk=pk)
            usages = CouponUsage.objects.filter(coupon=coupon)

            paginator = StandardResultsSetPagination()
            results = paginator.paginate_queryset(usages, request)

            serializer = CouponUsageSerializer(results, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Coupon.DoesNotExist:
            return Response(
                {"error": "Cupón no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )


class CampaignView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        campaigns = Campaign.objects.all().order_by("id")
        paginator = StandardResultsSetPagination()
        results = paginator.paginate_queryset(campaigns, request)

        serialized_campaigns = CampaignSerializer(results, many=True).data
        return paginator.get_paginated_response(serialized_campaigns)

    def post(self, request, format=None):
        serializer = CampaignSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CampaignSerializer(campaign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        try:
            campaign = Campaign.objects.get(pk=pk)
        except Campaign.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        campaign.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
