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


def clear_cart_coupons(user):
    """Limpiar cupones del carrito del usuario"""
    try:
        cart = Cart.objects.filter(user=user).first()
        if cart and hasattr(cart, "coupons"):
            cart.coupons.clear()
            logger.info(f"Cupones limpiados del carrito para usuario {user.id}")
        return True
    except Exception as e:
        logger.error(f"Error limpiando cupones del carrito: {str(e)}")
        return False


@shared_task()
def send_payment_success_email_task(email_address, subject=None, message=None):
    if not email_address:
        logger.error("No email address provided for payment success email.")
        return False

    subject = subject or _("Payment Successful")
    message = message or _("Thank you for purchasing our product!")

    try:
        send_mail(
            subject=subject,
            message=message,
            recipient_list=[email_address],
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        logger.info(
            f"Payment success email sent to {email_address}",
            extra={"email": email_address},
        )
        return True
    except Exception as e:
        logger.error(
            f"Error sending payment success email to {email_address}: {str(e)}",
            extra={"email": email_address, "error": str(e)},
        )
        return False


@shared_task(
    name="payments.tasks.handle_checkout_session_completed_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
)
def handle_checkout_session_completed_task(session_data):
    logger.info("Procesando evento checkout.session.completed")
    logger.info(f"Datos de la sesión: {session_data}")
    payment_id = session_data.get("metadata", {}).get("payment_id")
    logger.info(f"payment_id recibido: {payment_id}")
    order_id = session_data.get("metadata", {}).get("order_id")
    session_id = session_data.get("id")

    if not payment_id:
        logger.error("No payment_id found in session metadata")
        return

    if not order_id:
        logger.error("No order_id found in session metadata")
        return

    try:
        payment = Payment.objects.select_related("order").get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
        return

    try:
        logger.info(f"Actualizando estado del pago {payment_id} a COMPLETED")
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.save()

        logger.info(f"Actualizando estado de la orden {order_id} a COMPLETED")
        order.status = Order.OrderStatus.COMPLETED
        order.save()

        logger.info(
            f"Checkout session completed for payment {payment_id}",
            extra={
                "payment_id": payment_id,
                "order_id": order.id,
                "session_id": session_id,
            },
        )

        # Limpiar el carrito después del pago exitoso
        cart = Cart.objects.filter(user=payment.order.user).first()
        if cart:
            cart.items.all().delete()
            # Limpiar cupones del carrito
            clear_cart_coupons(payment.order.user)

        # Enviar email de éxito de pago
        if payment.order.user and payment.order.user.email and not payment.email_sent:
            send_payment_success_email_task.delay(payment.order.user.email)
            payment.email_sent = True
            payment.save()

        logger.info(f"Checkout session completed for payment {payment_id}")

    except Exception as e:
        logger.error(
            f"Error handling checkout.session.completed: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
                "session_id": session_id,
            },
        )
        raise


@shared_task
def handle_payment_intent_succeeded_task(payment_intent_data):
    payment_id = payment_intent_data.get("metadata", {}).get("payment_id")
    order_id = payment_intent_data.get("metadata", {}).get("order_id")

    if not payment_id:
        logger.error("No payment_id found in payment_intent metadata")
        return

    if not order_id:
        logger.error("No order_id found in payment_intent metadata")
        return

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
        return

    try:
        payment.status = Payment.PaymentStatus.COMPLETED
        payment.save()

        order.status = Order.OrderStatus.COMPLETED
        order.save()

        # Limpiar el carrito después del pago exitoso
        cart = Cart.objects.filter(user=payment.order.user).first()
        if cart:
            cart.items.all().delete()
            # Limpiar cupones del carrito
            clear_cart_coupons(payment.order.user)

        # Enviar email de éxito de pago
        if payment.order.user and payment.order.user.email and not payment.email_sent:
            send_payment_success_email_task.delay(payment.order.user.email)
            payment.email_sent = True
            payment.save()

        logger.info(
            f"Payment intent succeeded for payment {payment_id}",
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
            },
        )

    except Exception as e:
        logger.error(
            f"Error handling payment_intent.succeeded: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
            },
        )
        raise


@shared_task
def handle_payment_intent_payment_failed_task(payment_intent_data):
    payment_id = payment_intent_data.get("metadata", {}).get("payment_id")
    order_id = payment_intent_data.get("metadata", {}).get("order_id")

    if not payment_id:
        logger.error("No payment_id found in payment_intent metadata")
        return

    if not order_id:
        logger.error("No order_id found in payment_intent metadata")
        return

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
        return

    try:
        payment.status = Payment.PaymentStatus.FAILED
        payment.save()

        order.status = Order.OrderStatus.CANCELLED
        order.save()

        # Limpiar cupones del carrito cuando el pago falla
        clear_cart_coupons(payment.order.user)

        logger.warning(
            f"Payment intent failed for payment {payment_id}",
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
            },
        )

    except Exception as e:
        logger.error(
            f"Error handling payment_intent.payment_failed: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
            },
        )
        raise


@shared_task
def handle_refund_succeeded_task(charge_data):
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

            try:
                payment = Payment.objects.select_related("order").get(id=payment_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for refund: {payment_id}")
                return

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
            if payment.order:
                payment.order.status = Order.OrderStatus.CANCELLED
                payment.order.save()

            logger.info(f"Refund processed successfully for payment {payment_id}")

    except Exception as e:
        logger.error(
            f"Error processing refund: {str(e)}",
            exc_info=True,
            extra={"charge_data": charge_data, "error": str(e)},
        )
        raise


@shared_task
def send_subscription_welcome_email(email, subject=None, message=None):
    if not email:
        logger.error("No email address provided for subscription welcome email.")
        return False

    subject = subject or _("¡Bienvenido a tu nueva suscripción!")
    message = message or _("Gracias por suscribirte. Tu suscripción está activa.")

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(
            f"Subscription welcome email sent to {email}",
            extra={"email": email},
        )
        return True
    except Exception as e:
        logger.error(
            f"Error sending welcome email to {email}: {str(e)}",
            extra={"email": email, "error": str(e)},
        )
        return False


@shared_task
def send_subscription_canceled_email(email, end_date):
    if not email:
        logger.error("No email address provided for subscription cancellation email.")
        return False

    subject = _("Confirmación de cancelación de suscripción")
    message = _(
        "Tu suscripción ha sido cancelada. Tendrás acceso hasta {end_date}"
    ).format(end_date=end_date)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(
            f"Subscription cancellation email sent to {email}",
            extra={"email": email, "end_date": end_date},
        )
        return True
    except Exception as e:
        logger.error(
            f"Error sending cancellation email to {email}: {str(e)}",
            extra={"email": email, "error": str(e)},
        )
        return False


@shared_task
def handle_subscription_created_task(subscription_data):
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

            # Enviar email de bienvenida solo si el usuario existe y tiene email
            if (
                hasattr(subscription, "user")
                and subscription.user
                and subscription.user.email
            ):
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

        logger.info(
            f"Subscription {subscription.id} updated successfully",
            extra={"subscription_id": subscription.id},
        )

    except Subscription.DoesNotExist:
        logger.error(
            f"Subscription not found: {subscription_data.get('id')}",
            extra={"subscription_data": subscription_data},
        )
    except Exception as e:
        logger.error(
            f"Error updating subscription: {str(e)}",
            extra={"subscription_data": subscription_data, "error": str(e)},
            exc_info=True,
        )


@shared_task
def handle_subscription_deleted_task(subscription_data):
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

            # Enviar email de confirmación de cancelación solo si el usuario existe y tiene email
            if (
                hasattr(subscription, "user")
                and subscription.user
                and subscription.user.email
            ):
                send_subscription_canceled_email.delay(
                    subscription.user.email, end_date=subscription.current_period_end
                )

            logger.info(
                f"Subscription cancelled successfully: {subscription.stripe_subscription_id}",
                extra={
                    "subscription_id": subscription.id,
                    "user_id": getattr(subscription.user, "id", None),
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


@shared_task(
    name="payments.tasks.handle_manual_payment_cancellation_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
    bind=True,
)
def handle_manual_payment_cancellation_task(
    self, payment_id, user_id, reason="manual_cancellation"
):
    """Manejar cancelaciones manuales de pagos"""
    logger.info(f"Procesando cancelación manual para Payment ID: {payment_id}")

    try:
        # Importar aquí para evitar problemas de importación circular en contenedores
        from django.db import transaction
        from payments.models import Payment
        from orders.models import Order
        from cart.models import Cart

        payment = Payment.objects.select_related("order", "user").get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return {"status": "error", "message": "Payment not found"}

    try:
        with transaction.atomic():
            # Verificar que el pago no esté ya completado
            if payment.status == Payment.PaymentStatus.COMPLETED:
                logger.warning(
                    f"Payment {payment_id} already completed, skipping cancellation"
                )
                return {"status": "skipped", "message": "Payment already completed"}

            # Actualizar estado del pago
            payment.status = Payment.PaymentStatus.CANCELLED
            payment.error_message = f"Cancelación manual: {reason}"
            payment.save()

            # Actualizar estado de la orden
            payment.order.status = Order.OrderStatus.CANCELLED
            payment.order.save()

            # Liberar inventario usando el método del ViewSet
            try:
                from payments.views import PaymentViewSet

                viewset = PaymentViewSet()
                order_items = payment.order.orderitem_set.all()
                viewset.release_inventory(order_items)
                logger.info(f"Inventario liberado para orden {payment.order.id}")
            except Exception as e:
                logger.error(f"Error liberando inventario: {str(e)}")
                # No fallar la tarea por errores de inventario

            # Limpiar cupones del carrito
            try:
                cart = Cart.objects.filter(user=payment.order.user).first()
                if cart and hasattr(cart, "coupons"):
                    cart.coupons.clear()
                    logger.info(
                        f"Cupones limpiados del carrito para usuario {payment.order.user.id}"
                    )
            except Exception as e:
                logger.error(f"Error limpiando cupones: {str(e)}")
                # No fallar la tarea por errores de cupones

            logger.info(
                f"Manual payment cancellation processed for payment {payment_id}",
                extra={
                    "payment_id": payment_id,
                    "order_id": payment.order.id,
                    "user_id": user_id,
                    "reason": reason,
                },
            )

            return {
                "status": "success",
                "payment_id": payment_id,
                "order_id": str(payment.order.id),
                "reason": reason,
            }

    except Exception as e:
        logger.error(
            f"Error handling manual payment cancellation: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
                "user_id": user_id,
                "reason": reason,
            },
        )
        # Reintentar la tarea
        raise self.retry(countdown=60, max_retries=3)


@shared_task(
    name="payments.tasks.handle_checkout_session_expired_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
    bind=True,
)
def handle_checkout_session_expired_task(self, session_data):
    """Manejar la expiración de sesiones de checkout de Stripe"""
    logger.info("Procesando evento checkout.session.expired")
    logger.info(f"Datos de la sesión: {session_data}")

    payment_id = session_data.get("metadata", {}).get("payment_id")
    order_id = session_data.get("metadata", {}).get("order_id")
    session_id = session_data.get("id")

    if not payment_id:
        logger.error("No payment_id found in session metadata")
        return {"status": "error", "message": "No payment_id found"}

    if not order_id:
        logger.error("No order_id found in session metadata")
        return {"status": "error", "message": "No order_id found"}

    try:
        # Importar aquí para evitar problemas de importación circular en contenedores

        payment = Payment.objects.select_related("order", "user").get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return {"status": "error", "message": "Payment not found"}

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} not found")
        return {"status": "error", "message": "Order not found"}

    try:
        with transaction.atomic():
            # Solo actualizar si el pago no está ya completado
            if payment.status != Payment.PaymentStatus.COMPLETED:
                logger.info(f"Actualizando estado del pago {payment_id} a CANCELLED")
                payment.status = Payment.PaymentStatus.CANCELLED
                payment.error_message = "Sesión de checkout expirada"
                payment.save()

                logger.info(f"Actualizando estado de la orden {order_id} a CANCELLED")
                order.status = Order.OrderStatus.CANCELLED
                order.save()

                # Liberar inventario
                try:
                    from payments.views import PaymentViewSet

                    viewset = PaymentViewSet()
                    order_items = order.orderitem_set.all()
                    viewset.release_inventory(order_items)
                    logger.info(f"Inventario liberado para orden {order.id}")
                except Exception as e:
                    logger.error(f"Error liberando inventario: {str(e)}")

                # Limpiar cupones del carrito cuando la sesión expira
                try:
                    cart = Cart.objects.filter(user=payment.order.user).first()
                    if cart and hasattr(cart, "coupons"):
                        cart.coupons.clear()
                        logger.info(
                            f"Cupones limpiados del carrito para usuario {payment.order.user.id}"
                        )
                except Exception as e:
                    logger.error(f"Error limpiando cupones: {str(e)}")

                logger.info(
                    f"Checkout session expired for payment {payment_id}",
                    extra={
                        "payment_id": payment_id,
                        "order_id": order.id,
                        "session_id": session_id,
                    },
                )

                return {
                    "status": "success",
                    "payment_id": payment_id,
                    "order_id": str(order.id),
                    "session_id": session_id,
                }
            else:
                logger.info(
                    f"Payment {payment_id} already completed, skipping expiration handling"
                )
                return {
                    "status": "skipped",
                    "message": "Payment already completed",
                    "payment_id": payment_id,
                }

    except Exception as e:
        logger.error(
            f"Error handling checkout.session.expired: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
                "order_id": order_id,
                "session_id": session_id,
            },
        )
        # Reintentar la tarea
        raise self.retry(countdown=60, max_retries=3)


@shared_task
def handle_charge_succeeded_task(charge_data):
    logger.info("Procesando evento charge.succeeded")
    logger.info(f"Datos del cargo: {charge_data}")

    # Obtener payment_id directamente de los metadatos del cargo
    payment_id = charge_data.get("metadata", {}).get("payment_id")
    logger.info(f"payment_id recibido: {payment_id}")

    if not payment_id:
        logger.error("No payment_id found in charge metadata")
        return

    try:
        payment = Payment.objects.select_related("order").get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error(f"Payment with id {payment_id} not found")
        return

    try:
        with transaction.atomic():
            logger.info(f"Actualizando estado del pago {payment_id} a COMPLETED")
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.paid_at = timezone.now()
            payment.save()

            logger.info(
                f"Actualizando estado de la orden {payment.order.id} a COMPLETED"
            )
            payment.order.status = Order.OrderStatus.COMPLETED
            payment.order.save()

            # Limpiar el carrito después del pago exitoso
            cart = Cart.objects.filter(user=payment.order.user).first()
            if cart:
                cart.items.all().delete()
                # Limpiar cupones del carrito
                clear_cart_coupons(payment.order.user)

            # Enviar email de éxito de pago
            if (
                payment.order.user
                and payment.order.user.email
                and not payment.email_sent
            ):
                send_payment_success_email_task.delay(payment.order.user.email)
                payment.email_sent = True
                payment.save()

            logger.info(
                f"Charge succeeded for payment {payment_id}",
                extra={
                    "payment_id": payment_id,
                    "order_id": payment.order.id,
                },
            )

    except Exception as e:
        logger.error(
            f"Error handling charge.succeeded: {str(e)}",
            exc_info=True,
            extra={
                "payment_id": payment_id,
            },
        )
        raise


@shared_task(
    name="payments.tasks.periodic_clean_expired_sessions_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=300,  # 5 minutos entre reintentos
    bind=True,
)
def periodic_clean_expired_sessions_task(self):
    """Tarea periódica para limpiar sesiones expiradas automáticamente"""
    logger.info("Iniciando limpieza periódica de sesiones expiradas")

    try:
        import stripe
        from django.conf import settings
        from django.db import transaction
        from payments.models import Payment

        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Buscar pagos pendientes con sesiones de Stripe
        pending_payments = Payment.objects.filter(
            status=Payment.PaymentStatus.PENDING, stripe_session_id__isnull=False
        ).select_related("order", "user")

        logger.info(f"Verificando {pending_payments.count()} pagos pendientes")

        expired_count = 0
        error_count = 0

        for payment in pending_payments:
            try:
                # Verificar el estado de la sesión en Stripe
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)

                # Si la sesión ha expirado, procesar la cancelación
                if session.expires_at and session.expires_at < int(
                    timezone.now().timestamp()
                ):
                    logger.info(
                        f"Sesión expirada detectada: {payment.stripe_session_id}"
                    )
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1

                elif session.status == "expired":
                    logger.info(
                        f"Sesión marcada como expirada en Stripe: {payment.stripe_session_id}"
                    )
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1

            except stripe.error.InvalidRequestError:
                # La sesión no existe en Stripe, marcarla como cancelada
                logger.info(
                    f"Sesión no encontrada en Stripe: {payment.stripe_session_id}"
                )
                handle_manual_payment_cancellation_task.delay(
                    str(payment.id),
                    str(payment.user.id),
                    "sesión_no_encontrada_en_stripe",
                )
                expired_count += 1

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error verificando sesión {payment.stripe_session_id}: {str(e)}"
                )

        logger.info(
            f"Limpieza periódica completada: {expired_count} expiradas, {error_count} errores"
        )

        return {
            "status": "success",
            "expired_count": expired_count,
            "error_count": error_count,
            "total_checked": pending_payments.count(),
        }

    except Exception as e:
        logger.error(f"Error en limpieza periódica de sesiones: {str(e)}")
        # Reintentar la tarea
        raise self.retry(countdown=300, max_retries=3)


@shared_task(
    name="payments.tasks.clean_expired_sessions_task",
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=300,  # 5 minutos entre reintentos
    bind=True,
)
def clean_expired_sessions_task(self):
    """Tarea para limpiar sesiones expiradas (ejecutar manualmente o programada)"""
    logger.info("Iniciando limpieza de sesiones expiradas")
    
    try:
        import stripe
        from django.conf import settings
        from django.db import transaction
        from payments.models import Payment
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Buscar pagos pendientes con sesiones de Stripe
        pending_payments = Payment.objects.filter(
            status=Payment.PaymentStatus.PENDING, stripe_session_id__isnull=False
        ).select_related("order", "user")
        
        logger.info(f"Verificando {pending_payments.count()} pagos pendientes")
        
        expired_count = 0
        error_count = 0
        
        for payment in pending_payments:
            try:
                # Verificar el estado de la sesión en Stripe
                session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
                
                # Si la sesión ha expirado, procesar la cancelación
                if session.expires_at and session.expires_at < int(
                    timezone.now().timestamp()
                ):
                    logger.info(
                        f"Sesión expirada detectada: {payment.stripe_session_id}"
                    )
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1
                    
                elif session.status == "expired":
                    logger.info(
                        f"Sesión marcada como expirada en Stripe: {payment.stripe_session_id}"
                    )
                    handle_checkout_session_expired_task.delay(session.to_dict())
                    expired_count += 1
                    
            except stripe.error.InvalidRequestError:
                # La sesión no existe en Stripe, marcarla como cancelada
                logger.info(
                    f"Sesión no encontrada en Stripe: {payment.stripe_session_id}"
                )
                handle_manual_payment_cancellation_task.delay(
                    str(payment.id),
                    str(payment.user.id),
                    "sesión_no_encontrada_en_stripe",
                )
                expired_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error verificando sesión {payment.stripe_session_id}: {str(e)}"
                )
        
        logger.info(
            f"Limpieza completada: {expired_count} expiradas, {error_count} errores"
        )
        
        # Programar la siguiente ejecución si es necesario
        if expired_count > 0 or error_count > 0:
            # Si se encontraron problemas, ejecutar de nuevo en 5 minutos
            clean_expired_sessions_task.apply_async(countdown=300)
        else:
            # Si todo está bien, ejecutar de nuevo en 15 minutos
            clean_expired_sessions_task.apply_async(countdown=900)
        
        return {
            "status": "success",
            "expired_count": expired_count,
            "error_count": error_count,
            "total_checked": pending_payments.count(),
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de sesiones: {str(e)}")
        # Reintentar en 10 minutos si hay error
        clean_expired_sessions_task.apply_async(countdown=600)
        raise self.retry(countdown=600, max_retries=3)
