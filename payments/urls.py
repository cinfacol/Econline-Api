from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CheckoutAPIView,
    PaymentViewSet,
    StripeCheckoutSessionCreateAPIView,
    StripeWebhookAPIView,
)

app_name = "payment"

router = DefaultRouter()
router.register(r"", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "stripe/create-checkout-session/<int:order_id>/",
        StripeCheckoutSessionCreateAPIView.as_view(),
        name="checkout_session",
    ),
    path("stripe/webhook/", StripeWebhookAPIView.as_view(), name="stripe_webhook"),
    path("checkout/<int:pk>/", CheckoutAPIView.as_view(), name="checkout"),
]

""" urlpatterns = [
    path("get-payment-total/", GetPaymentTotalView.as_view()),
    path("get-token/", GenerateTokenView.as_view()),
    path("make-payment/", ProcessPaymentView.as_view()),
] """
