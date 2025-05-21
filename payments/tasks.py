from celery import shared_task
from decimal import Decimal
from .models import Payment, Refund, Subscription, SubscriptionHistory
from django.utils import timezone
from orders.models import Order
from cart.models import Cart
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@shared_task()
def send_payment_success_email_task(email_address):
    """
    Celery task to send an email when payment is successfull
    """
    try:
        send_mail(
            subject=_("Payment Successful"),
            message=_("Thank you for purchasing our product!"),
            recipient_list=[email_address],
            from_email=settings.EMAIL_HOST_USER,
        )
    except Exception as e:
        logger.error(
            f"Error sending payment success email to {email_address}: {str(e)}"
        )


@shared_task(
    name="payments.tasks.handle_checkout_session_completed_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
)
def handle_checkout_session_completed_task(session_data):
    """Maneja el evento checkout.session.completed de forma asíncrona"""
    try:
        payment_id = session_data.get("metadata", {}).get("payment_id")
        if not payment_id:
            logger.error("No payment_id found in session metadata")
            return

        payment = Payment.objects.select_related("order").get(id=payment_id)
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.save()

        order_id = session_data.get("metadata", {}).get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = Order.OrderStatus.COMPLETED
        order.save()

        logger.info(
            f"Checkout session completed for payment {payment_id}",
            extra={
                "payment_id": payment_id,
                "order_id": order.id,
                "session_id": session_data.get("id"),
            },
        )

        # Limpiar el carrito después del pago exitoso
        cart = Cart.objects.filter(user=payment.order.user).first()
        if cart:
            cart.items.all().delete()

        logger.info(f"Checkout session completed for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
    except Exception as e:
        logger.error(
            f"Error handling checkout.session.completed: {str(e)}", exc_info=True
        )
    raise


@shared_task
def handle_payment_intent_succeeded_task(payment_intent_data):
    """Maneja el evento payment_intent.succeeded de forma asíncrona"""
    try:
        payment_id = payment_intent_data.get("metadata", {}).get("payment_id")
        payment = Payment.objects.get(id=payment_id)
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.save()

        order_id = payment_intent_data.get("metadata", {}).get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = Order.OrderStatus.COMPLETED
        order.save()

        # Limpiar el carrito después del pago exitoso
        cart = Cart.objects.filter(user=payment.order.user).first()
        if cart:
            cart.items.all().delete()

        logger.info(f"Payment intent succeeded for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
    except Exception as e:
        logger.error(f"Error handling payment_intent.succeeded: {str(e)}")


@shared_task
def handle_payment_intent_payment_failed_task(payment_intent_data):
    """Maneja el evento payment_intent.payment_failed de forma asíncrona"""
    try:
        payment_id = payment_intent_data.get("metadata", {}).get("payment_id")
        payment = Payment.objects.get(id=payment_id)
        payment.status = Payment.PaymentStatus.FAILED
        payment.save()

        order_id = payment_intent_data.get("metadata", {}).get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = Order.OrderStatus.CANCELLED
        order.save()

        logger.warning(f"Payment intent failed for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
    except Exception as e:
        logger.error(f"Error handling payment_intent.payment_failed: {str(e)}")


@shared_task
def handle_refund_succeeded_task(charge_data):
    """
    Maneja el evento de reembolso exitoso
    """
    try:
        with transaction.atomic():
            # Obtener el ID del pago del metadata del cargo
            payment_id = (
                charge_data.get("payment_intent", {})
                .get("metadata", {})
                .get("payment_id")
            )

            if not payment_id:
                logger.error("No payment_id found in refund metadata")
                return

            payment = Payment.objects.select_related("order").get(id=payment_id)

            # Crear registro de reembolso
            refund_amount = (
                Decimal(charge_data.get("amount_refunded", 0)) / 100
            )  # Convertir de centavos a unidad

            Refund.objects.create(
                payment=payment,
                amount=refund_amount,
                stripe_refund_id=charge_data.get("id"),
                reason=charge_data.get("reason", "customer_requested"),
                status="completed",
            )

            # Actualizar estado del pago
            payment.status = Payment.PaymentStatus.REFUNDED
            payment.save()

            # Actualizar estado de la orden
            payment.order.status = Order.OrderStatus.CANCELLED
            payment.order.save()

            logger.info(f"Refund processed successfully for payment {payment_id}")

    except Payment.DoesNotExist:
        logger.error(f"Payment not found for refund: {payment_id}")
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")


@shared_task
def send_subscription_welcome_email(email):
    """Envía email de bienvenida para nuevas suscripciones"""
    try:
        send_mail(
            subject=_("¡Bienvenido a tu nueva suscripción!"),
            message=_("Gracias por suscribirte. Tu suscripción está activa."),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")


@shared_task
def send_subscription_canceled_email(email, end_date):
    """Envía email de confirmación de cancelación"""
    try:
        send_mail(
            subject=_("Confirmación de cancelación de suscripción"),
            message=_(
                f"Tu suscripción ha sido cancelada. Tendrás acceso hasta {end_date}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
    except Exception as e:
        logger.error(f"Error sending cancellation email: {str(e)}")


@shared_task
def handle_subscription_created_task(subscription_data):
    """
    Maneja el evento de creación de suscripción
    """
    try:
        with transaction.atomic():
            customer_id = subscription_data.get("customer")
            subscription_id = subscription_data.get("id")

            subscription = Subscription.objects.create(
                stripe_subscription_id=subscription_id,
                stripe_customer_id=customer_id,
                stripe_price_id=subscription_data.get("plan", {}).get("id"),
                status=subscription_data.get("status").upper(),
                current_period_start=timezone.datetime.fromtimestamp(
                    subscription_data.get("current_period_start")
                ),
                current_period_end=timezone.datetime.fromtimestamp(
                    subscription_data.get("current_period_end")
                ),
                trial_start=(
                    timezone.datetime.fromtimestamp(
                        subscription_data.get("trial_start")
                    )
                    if subscription_data.get("trial_start")
                    else None
                ),
                trial_end=(
                    timezone.datetime.fromtimestamp(subscription_data.get("trial_end"))
                    if subscription_data.get("trial_end")
                    else None
                ),
            )

            # Enviar email de bienvenida
            send_subscription_welcome_email.delay(subscription.user.email)

            logger.info(
                f"Subscription created: {subscription_id} for customer {customer_id}"
            )

    except Exception as e:
        logger.error(
            f"Error processing subscription creation: {str(e)}",
            extra={"subscription_data": subscription_data, "error": str(e)},
            exc_info=True,
        )
        raise


@shared_task
def handle_subscription_updated_task(subscription_data):
    """Maneja actualizaciones de suscripción"""
    try:
        subscription = Subscription.objects.get(
            stripe_subscription_id=subscription_data.get("id")
        )

        subscription.status = subscription_data.get("status").upper()
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            subscription_data.get("current_period_start")
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            subscription_data.get("current_period_end")
        )
        subscription.save()

        logger.info(f"Subscription {subscription.id} updated successfully")

    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {subscription_data.get('id')}")
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")


@shared_task
def handle_subscription_deleted_task(subscription_data):
    """
    Maneja el evento de eliminación/cancelación de suscripción.
    """
    try:
        with transaction.atomic():
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_data.get("id")
            )

            # Actualizar el estado de la suscripción
            subscription.status = Subscription.SubscriptionStatus.CANCELED
            subscription.canceled_at = timezone.now()
            subscription.save()

            # Registrar la cancelación en el histórico si tienes una tabla para ello
            SubscriptionHistory.objects.create(
                subscription=subscription,
                action="CANCELED",
                metadata={
                    "reason": subscription_data.get("cancellation_reason"),
                    "canceled_at": timezone.now().isoformat(),
                },
            )

            # Enviar email de confirmación de cancelación
            send_subscription_canceled_email.delay(
                subscription.user.email, end_date=subscription.current_period_end
            )

            logger.info(
                f"Subscription cancelled successfully: {subscription.stripe_subscription_id}",
                extra={
                    "subscription_id": subscription.id,
                    "user_id": subscription.user.id,
                    "end_date": subscription.current_period_end,
                },
            )

    except Subscription.DoesNotExist:
        logger.error(
            f"Subscription not found: {subscription_data.get('id')}",
            extra={"subscription_data": subscription_data},
        )
    except Exception as e:
        logger.error(
            f"Error processing subscription deletion: {str(e)}",
            extra={"subscription_data": subscription_data, "error": str(e)},
            exc_info=True,
        )
        raise
