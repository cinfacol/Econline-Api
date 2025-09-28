import logging
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cart.models import Cart
from orders.models import Order

from .models import Payment, Refund, Subscription, SubscriptionHistory

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

    # Guardar dirección de envío de Stripe en la orden (después de obtener payment, order y session_id)
    try:
        import stripe

        from orders.models import Address

        stripe.api_key = settings.STRIPE_SECRET_KEY
        if session_id:
            stripe_session = stripe.checkout.Session.retrieve(session_id)
            shipping_details = getattr(stripe_session, "shipping_details", None)
            logger.info(f"shipping_details recibidos de Stripe: {shipping_details}")
            if shipping_details and hasattr(order, "user") and order.user:
                shipping_address = shipping_details.address
                logger.info(f"shipping_address extraído: {shipping_address}")
                address, created = Address.objects.get_or_create(
                    address_line_1=shipping_address.line1,
                    address_line_2=shipping_address.line2,
                    city=shipping_address.city,
                    state_province_region=shipping_address.state,
                    postal_zip_code=shipping_address.postal_code,
                    country_region=shipping_address.country,
                    user=order.user,
                )
                logger.info(
                    f"Address {'creada' if created else 'encontrada'}: {address}"
                )
                logger.info(
                    f"[PRE] order.address antes de asociar: {order.address.id if order.address else None}"
                )
                if not order.address or order.address != address:
                    order.address = address
                    order.save()
                    logger.info(f"Shipping address asociada a la orden {order.id}")
                else:
                    logger.info(
                        f"La orden {order.id} ya tiene la dirección asociada correctamente"
                    )
                # Log SIEMPRE el estado final
                logger.info(
                    f"[POST] Estado final order.address: {order.address.id if order.address else None} | Datos: {order.address.address_line_1 if order.address else None}, {order.address.address_line_2 if order.address else None}"
                )
            else:
                logger.warning(
                    "No se encontraron shipping_details o el usuario de la orden no está definido"
                )
        else:
            logger.warning(
                "No se recibió session_id para recuperar la sesión de Stripe"
            )
    except Exception as e:
        logger.error(
            f"Error asociando dirección de envío a la orden: {str(e)}", exc_info=True
        )

    try:
        # Guardar el Payment Intent ID si está disponible en la sesión
        if session_id:
            try:
                import stripe

                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe_session = stripe.checkout.Session.retrieve(session_id)
                if (
                    hasattr(stripe_session, "payment_intent")
                    and stripe_session.payment_intent
                ):
                    payment.stripe_payment_intent_id = stripe_session.payment_intent
                    logger.info(
                        f"Payment Intent ID guardado: {stripe_session.payment_intent}"
                    )
            except Exception as e:
                logger.warning(f"No se pudo obtener Payment Intent ID: {str(e)}")

        # Actualizar solo si no está ya completado (evitar condición de carrera)
        if payment.status != Payment.PaymentStatus.COMPLETED:
            logger.info(f"Actualizando estado del pago {payment_id} a COMPLETED")
            payment.status = Payment.PaymentStatus.COMPLETED
            payment.paid_at = timezone.now()
            payment.save()
        else:
            logger.info(f"Pago {payment_id} ya estaba COMPLETED")

        if order.status != Order.OrderStatus.COMPLETED:
            logger.info(f"Actualizando estado de la orden {order_id} a COMPLETED")
            order.status = Order.OrderStatus.COMPLETED
            order.save()
        else:
            logger.info(f"Orden {order_id} ya estaba COMPLETED")

        logger.info(
            f"Checkout session completed for payment {payment_id}",
            extra={
                "payment_id": payment_id,
                "order_id": order.id,
                "session_id": session_id,
            },
        )

        # Limpiar el carrito después del pago exitoso (corregir variable incorrecta)
        if order and order.user:
            cart = Cart.objects.filter(user=order.user).first()
            if cart and cart.items.exists():
                cart.items.all().delete()
                # Limpiar cupones del carrito
                clear_cart_coupons(order.user)
                logger.info(f"Carrito limpiado para usuario {order.user.id}")
            else:
                logger.info("Carrito ya estaba limpio o no existe")

        # El envío de email de éxito de pago se realiza solo en el handler de charge.succeeded

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

    # Guardar dirección de envío si viene en el payment_intent
    try:
        shipping_details = payment_intent_data.get("shipping")
        logger.info(f"shipping_details recibidos de payment_intent: {shipping_details}")
        if shipping_details and hasattr(order, "user") and order.user:
            shipping_address = shipping_details.get("address")
            if shipping_address:
                from orders.models import Address

                address, created = Address.objects.get_or_create(
                    address_line_1=shipping_address.get("line1", ""),
                    address_line_2=shipping_address.get("line2", ""),
                    city=shipping_address.get("city", ""),
                    state_province_region=shipping_address.get("state", ""),
                    postal_zip_code=shipping_address.get("postal_code", ""),
                    country_region=shipping_address.get("country", ""),
                    user=order.user,
                )
                logger.info(
                    f"Address {'creada' if created else 'encontrada'}: {address}"
                )
                logger.info(
                    f"[PRE] order.address antes de asociar: {order.address.id if order.address else None}"
                )
                if not order.address or order.address != address:
                    order.address = address
                    order.save()
                    logger.info(f"Shipping address asociada a la orden {order.id}")
                else:
                    logger.info(
                        f"La orden {order.id} ya tiene la dirección asociada correctamente"
                    )
                # Log SIEMPRE el estado final
                logger.info(
                    f"[POST] Estado final order.address: {order.address.id if order.address else None} | Datos: {order.address.address_line_1 if order.address else None}, {order.address.address_line_2 if order.address else None}"
                )
            else:
                logger.warning("No se encontró address dentro de shipping_details")
        else:
            logger.warning(
                "No se encontraron shipping_details o el usuario de la orden no está definido"
            )
    except Exception as e:
        logger.error(
            f"Error asociando dirección de envío a la orden desde payment_intent: {str(e)}",
            exc_info=True,
        )

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

        # El envío de email de éxito de pago se realiza solo en el handler de charge.succeeded

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
    logger.info("Procesando evento charge.refunded")
    logger.info(f"Datos del cargo de reembolso: {charge_data}")

    try:
        with transaction.atomic():
            payment = None

            # Método 1: Buscar por payment_id en metadata del charge
            payment_id = charge_data.get("metadata", {}).get("payment_id")
            if payment_id:
                try:
                    payment = Payment.objects.select_related("order").get(id=payment_id)
                    logger.info(
                        f"Payment encontrado por metadata payment_id: {payment_id}"
                    )
                except Payment.DoesNotExist:
                    logger.warning(
                        f"Payment no encontrado con metadata payment_id: {payment_id}"
                    )

            # Método 2: Buscar por payment_intent del charge si no se encontró por metadata
            if not payment and charge_data.get("payment_intent"):
                try:
                    payment_intent_id = charge_data.get("payment_intent")
                    payment = Payment.objects.select_related("order").get(
                        stripe_payment_intent_id=payment_intent_id
                    )
                    logger.info(
                        f"Payment encontrado por payment_intent_id: {payment_intent_id}"
                    )
                except Payment.DoesNotExist:
                    logger.warning(
                        f"Payment no encontrado con payment_intent_id: {payment_intent_id}"
                    )

            # Método 3: Buscar en metadata del payment_intent si está disponible
            if not payment:
                try:
                    import stripe

                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    payment_intent_id = charge_data.get("payment_intent")
                    if payment_intent_id:
                        payment_intent = stripe.PaymentIntent.retrieve(
                            payment_intent_id
                        )
                        payment_id = payment_intent.metadata.get("payment_id")
                        if payment_id:
                            payment = Payment.objects.select_related("order").get(
                                id=payment_id
                            )
                            logger.info(
                                f"Payment encontrado via PaymentIntent metadata: {payment_id}"
                            )
                except Exception as e:
                    logger.warning(
                        f"Error buscando payment via PaymentIntent: {str(e)}"
                    )

            if not payment:
                logger.error(
                    f"No se pudo encontrar el pago para el reembolso. Charge ID: {charge_data.get('id')}"
                )
                return

            # Crear registro de reembolso
            refund_amount = (
                Decimal(charge_data.get("amount_refunded", 0)) / 100
            )  # Convertir de centavos a unidad

            refund = Refund.objects.create(
                payment=payment,
                user=payment.user,  # Asociar al usuario del pago
                amount=refund_amount,
                currency=payment.currency,  # Usar la moneda del pago original
                stripe_refund_id=charge_data.get("id"),
                reason=charge_data.get("reason", "customer_requested"),
                status="completed",
            )
            logger.info(
                f"Registro de reembolso creado: {refund.id} por ${refund_amount}"
            )

            # Actualizar estado del pago
            old_payment_status = payment.status
            payment.status = Payment.PaymentStatus.REFUNDED
            payment.save()
            logger.info(
                f"Payment status actualizado de {old_payment_status} a REFUNDED"
            )

            # Actualizar estado de la orden
            if payment.order:
                old_order_status = payment.order.status
                payment.order.status = Order.OrderStatus.CANCELLED
                payment.order.save()
                logger.info(
                    f"Order status actualizado de {old_order_status} a CANCELLED"
                )

                # Liberar inventario cuando se hace reembolso
                try:
                    from payments.views import PaymentViewSet

                    viewset = PaymentViewSet()
                    order_items = payment.order.orderitem_set.all()
                    if order_items.exists():
                        viewset.release_inventory(order_items)
                        logger.info(
                            f"Inventario liberado para {order_items.count()} items de la orden {payment.order.id}"
                        )
                except Exception as e:
                    logger.error(f"Error liberando inventario en reembolso: {str(e)}")

                # Limpiar cupones del carrito
                try:
                    clear_cart_coupons(payment.user)
                except Exception as e:
                    logger.error(f"Error limpiando cupones en reembolso: {str(e)}")

            # Enviar email de notificación de reembolso
            if payment.user and payment.user.email:
                send_refund_notification_email.delay(
                    payment.user.email,
                    refund_amount,
                    payment.order.id if payment.order else payment.id,
                    payment.currency,
                )

            logger.info(
                f"Refund processed successfully for payment {payment.id}",
                extra={
                    "payment_id": str(payment.id),
                    "order_id": str(payment.order.id) if payment.order else None,
                    "refund_amount": float(refund_amount),
                    "stripe_refund_id": charge_data.get("id"),
                    "user_id": str(payment.user.id),
                },
            )

    except Exception as e:
        logger.error(
            f"Error processing refund: {str(e)}",
            exc_info=True,
            extra={"charge_data": charge_data, "error": str(e)},
        )
        raise


@shared_task
def send_refund_notification_email(email, refund_amount, order_ref, currency="USD"):
    """Enviar email de notificación de reembolso al usuario"""
    if not email:
        logger.error("No email address provided for refund notification email.")
        return False

    subject = _("Confirmación de reembolso - Pedido #{order_ref}").format(
        order_ref=order_ref
    )
    message = _(
        "Hola,\n\n"
        "Te confirmamos que tu reembolso ha sido procesado exitosamente.\n\n"
        "Detalles del reembolso:\n"
        "- Pedido: #{order_ref}\n"
        "- Monto reembolsado: {refund_amount} {currency}\n\n"
        "El reembolso aparecerá en tu método de pago original en los próximos 5-10 días hábiles.\n\n"
        "Si tienes alguna pregunta, no dudes en contactarnos.\n\n"
        "Gracias por tu comprensión.\n\n"
        "Equipo de VirtuelLine"
    ).format(order_ref=order_ref, refund_amount=refund_amount, currency=currency)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        logger.info(
            f"Refund notification email sent to {email}",
            extra={
                "email": email,
                "refund_amount": refund_amount,
                "order_ref": order_ref,
                "currency": currency,
            },
        )
        return True
    except Exception as e:
        logger.error(
            f"Error sending refund notification email to {email}: {str(e)}",
            extra={
                "email": email,
                "refund_amount": refund_amount,
                "order_ref": order_ref,
                "error": str(e),
            },
        )
        return False


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

        from cart.models import Cart
        from orders.models import Order
        from payments.models import Payment

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
            # Guardar dirección de envío si viene en el charge
            try:
                shipping_details = charge_data.get("shipping")
                logger.info(f"shipping_details recibidos de charge: {shipping_details}")
                if (
                    shipping_details
                    and hasattr(payment.order, "user")
                    and payment.order.user
                ):
                    shipping_address = shipping_details.get("address")
                    if shipping_address:
                        from orders.models import Address

                        address, created = Address.objects.get_or_create(
                            address_line_1=shipping_address.get("line1", ""),
                            address_line_2=shipping_address.get("line2", ""),
                            city=shipping_address.get("city", ""),
                            state_province_region=shipping_address.get("state", ""),
                            postal_zip_code=shipping_address.get("postal_code", ""),
                            country_region=shipping_address.get("country", ""),
                            user=payment.order.user,
                        )
                        logger.info(
                            f"Address {'creada' if created else 'encontrada'}: {address}"
                        )
                        logger.info(
                            f"[PRE] payment.order.address antes de asociar: {payment.order.address.id if payment.order.address else None}"
                        )
                        if (
                            not payment.order.address
                            or payment.order.address != address
                        ):
                            payment.order.address = address
                            payment.order.save()
                            logger.info(
                                f"Shipping address asociada a la orden {payment.order.id}"
                            )
                        else:
                            logger.info(
                                f"La orden {payment.order.id} ya tiene la dirección asociada correctamente"
                            )
                        # Log SIEMPRE el estado final
                        logger.info(
                            f"[POST] Estado final order.address: {payment.order.address.id if payment.order.address else None} | Datos: {payment.order.address.address_line_1 if payment.order.address else None}, {payment.order.address.address_line_2 if payment.order.address else None}"
                        )
                    else:
                        logger.warning(
                            "No se encontró address dentro de shipping_details"
                        )
                else:
                    logger.warning(
                        "No se encontraron shipping_details o el usuario de la orden no está definido"
                    )
            except Exception as e:
                logger.error(
                    f"Error asociando dirección de envío a la orden desde charge: {str(e)}",
                    exc_info=True,
                )

            # Actualizar solo si no está ya completado (evitar condición de carrera)
            if payment.status != Payment.PaymentStatus.COMPLETED:
                logger.info(f"Actualizando estado del pago {payment_id} a COMPLETED")
                payment.status = Payment.PaymentStatus.COMPLETED
                payment.paid_at = timezone.now()
                payment.save()
            else:
                logger.info(f"Pago {payment_id} ya estaba COMPLETED")

            if payment.order.status != Order.OrderStatus.COMPLETED:
                logger.info(
                    f"Actualizando estado de la orden {payment.order.id} a COMPLETED"
                )
                payment.order.status = Order.OrderStatus.COMPLETED
                payment.order.save()
            else:
                logger.info(f"Orden {payment.order.id} ya estaba COMPLETED")

            # Limpiar el carrito después del pago exitoso (solo si no se ha limpiado ya)
            if payment.order and payment.order.user:
                cart = Cart.objects.filter(user=payment.order.user).first()
                if cart and cart.items.exists():
                    cart.items.all().delete()
                    # Limpiar cupones del carrito
                    clear_cart_coupons(payment.order.user)
                    logger.info(
                        f"Carrito limpiado para usuario {payment.order.user.id}"
                    )
                else:
                    logger.info("Carrito ya estaba limpio")

            # Enviar email de éxito de pago de forma atómica
            if payment.order.user and payment.order.user.email:
                updated = Payment.objects.filter(
                    id=payment.id, email_sent=False
                ).update(email_sent=True)
                if updated:
                    send_payment_success_email_task.delay(payment.order.user.email)

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
