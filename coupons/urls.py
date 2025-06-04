from django.urls import path
from .views import (
    CheckCouponView,
    CampaignView,
    CouponListView,
    CouponDetailView,
    CouponUsageView,
)

urlpatterns = [
    # Endpoints existentes
    path("check/", CheckCouponView.as_view(), name="check-coupon"),
    path("campaign/", CampaignView.as_view(), name="campaign-list"),
    # Nuevos endpoints para cupones
    path("coupons/", CouponListView.as_view(), name="coupon-list"),
    path("coupons/<uuid:id>/", CouponDetailView.as_view(), name="coupon-detail"),
    path("coupons/<uuid:id>/usage/", CouponUsageView.as_view(), name="coupon-usage"),
]
