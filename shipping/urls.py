from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShippingViewSet

router = DefaultRouter()
router.register("", ShippingViewSet, basename="shipping")

urlpatterns = [
    path("", include(router.urls)),
]
