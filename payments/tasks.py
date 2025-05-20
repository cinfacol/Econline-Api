from celery import shared_task
from .models import Payment
from orders.models import Order
from cart.models import Cart
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


@shared_task
def handle_checkout_session_completed_task(session_data):
    """Maneja el evento checkout.session.completed de forma asíncrona"""
    try:
        payment_id = session_data.get("metadata", {}).get("payment_id")
        payment = Payment.objects.get(id=payment_id)
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.save()

        order_id = session_data.get("metadata", {}).get("order_id")
        order = Order.objects.get(id=order_id)
        order.status = Order.OrderStatus.COMPLETED
        order.save()

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
        logger.error(f"Error handling checkout.session.completed: {str(e)}")


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
