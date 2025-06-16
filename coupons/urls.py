from django.urls import path
from .views import (
    CouponListView,
    CheckCouponView,
    CouponDetailView,
    CouponUsageView,
    CampaignView,
)

urlpatterns = [
    # Endpoints para cupones
    path("/", CouponListView.as_view(), name="coupon-list"),
    path("check/", CheckCouponView.as_view(), name="check-coupon"),
    path("<uuid:id>/", CouponDetailView.as_view(), name="coupon-detail"),
    path("<uuid:id>/usage/", CouponUsageView.as_view(), name="coupon-usage"),
    # Endpoint para campañas
    path("campaign/", CampaignView.as_view(), name="campaign-list"),
]
