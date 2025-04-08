from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet

router = DefaultRouter()
router.register(r"", PaymentViewSet, basename="payments")

urlpatterns = [
    # Rutas específicas primero
    path(
        "calculate-total/",
        PaymentViewSet.as_view({"get": "calculate_total"}),
        name="calculate-total",
    ),
    path(
        "create-checkout-session/",
        PaymentViewSet.as_view({"post": "create_checkout_session"}),
        name="create-checkout-session",
    ),
    path(
        "<uuid:id>/process/",
        PaymentViewSet.as_view({"post": "process"}),
        name="process-payment",
    ),
    path(
        "<uuid:id>/verify/",
        PaymentViewSet.as_view({"get": "verify"}),
        name="verify-payment",
    ),
    # Webhook para Stripe
    path(
        "webhook/stripe/",
        PaymentViewSet.as_view({"post": "stripe_webhook"}),
        name="stripe-webhook",
    ),
    path(
        "client-token/",
        PaymentViewSet.as_view({"get": "client_token"}),
        name="client-token",
    ),
] + router.urls
