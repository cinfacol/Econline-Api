from django.urls import path
from .views import (
    CheckCouponView,
    CampaignView,
    CouponListView,
    CouponDetailView,
    CouponUsageView,
)

urlpatterns = [
    # Endpoints para cupones
    path("check/", CheckCouponView.as_view(), name="check-coupon"),
    path("", CouponListView.as_view(), name="coupon-list"),
    path("<uuid:id>/", CouponDetailView.as_view(), name="coupon-detail"),
    path("<uuid:id>/usage/", CouponUsageView.as_view(), name="coupon-usage"),
    # Endpoint para campañas
    path("campaign/", CampaignView.as_view(), name="campaign-list"),
]
