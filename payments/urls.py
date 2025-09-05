from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet

router = DefaultRouter()
router.register(r"", PaymentViewSet, basename="payments")

# Asegurarnos de que las rutas específicas vayan antes que las rutas del router
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
        "stripe_webhook/",
        PaymentViewSet.as_view({"post": "stripe_webhook"}),
        name="stripe-webhook",
    ),
    # Webhook de prueba
    path(
        "webhook-test/",
        PaymentViewSet.as_view({"post": "webhook_test"}),
        name="webhook-test",
    ),
    path(
        "payment-methods/",
        PaymentViewSet.as_view({"get": "payment_methods"}),
        name="payment-methods",
    ),
    path(
        "get-payment-by-session/",
        PaymentViewSet.as_view({"get": "get_payment_by_session"}),
        name="get-payment-by-session",
    ),
    path(
        "<uuid:id>/refund/",
        PaymentViewSet.as_view({"post": "refund"}),
        name="refund-payment",
    ),
    path(
        "subscriptions/create/",
        PaymentViewSet.as_view({"post": "create_subscription"}),
        name="create-subscription",
    ),
    path(
        "subscriptions/current/",
        PaymentViewSet.as_view({"get": "current_subscription"}),
        name="current-subscription",
    ),
    path(
        "subscriptions/<uuid:id>/cancel/",
        PaymentViewSet.as_view({"post": "cancel_subscription"}),
        name="cancel-subscription",
    ),
] + router.urls
