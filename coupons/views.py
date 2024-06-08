from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Coupon, FixedPriceCoupon, PercentageCoupon, Campaign
from .serializers import CouponSerializer, CampaignSerializer
from inventory.models import Inventory


class CheckCouponView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        coupon_name = request.query_params.get("name")
        inventory_id = request.query_params.get("inventory")

        try:
            coupon = Coupon.objects.get(name=coupon_name)

            # Check if the coupon belongs to the specified inventory
            if str(inventory_id) != str(coupon.inventory.id):
                return Response(
                    {"error": "Coupon is not valid for this inventory"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if coupon.fixed_price_coupon:
                if coupon.fixed_price_coupon.uses > 0:
                    serialized_coupon = CouponSerializer(coupon).data
                    return Response(
                        {
                            "coupon": serialized_coupon,
                            "type": "fixed",
                            "discount": coupon.fixed_price_coupon.discount_price,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": "Coupon code has no uses left"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            if coupon.percentage_coupon:
                if coupon.percentage_coupon.uses > 0:
                    serialized_coupon = CouponSerializer(coupon).data
                    return Response(
                        {
                            "coupon": serialized_coupon,
                            "type": "percentage",
                            "discount": coupon.percentage_coupon.discount_percentage,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": "Coupon code has no uses left"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        except NotFound:
            return Response(
                {"error": "Coupon not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CampaignView(APIView):
    def get(self, request, format=None):
        campaigns = Campaign.objects.all().order_by("id")

        # Pagination using PageNumberPagination
        paginator = PageNumberPagination()
        results = paginator.paginate_queryset(campaigns, request)

        serialized_campaigns = CampaignSerializer(results, many=True).data
        response_data = {
            "campaigns": serialized_campaigns,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
        }

        return Response(response_data, status=status.HTTP_200_OK)

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
