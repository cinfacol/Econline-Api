"""
Fase 1: Logging Estructurado y Métricas Básicas
Implementación gradual del flujo de pagos optimizado
"""

import time

import stripe
import structlog
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

# Configurar logging estructurado
logger = structlog.get_logger()


class PaymentMetrics:
    """Métricas básicas para monitoreo de pagos"""

    @staticmethod
    def record_payment_attempt(payment_method, user_id):
        """Registrar intento de pago"""
        cache_key = f"payment_attempts_{payment_method}_{user_id}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=3600)  # 1 hora

        logger.info(
            "payment_attempt_recorded",
            payment_method=payment_method,
            user_id=user_id,
            attempts=attempts,
        )

    @staticmethod
    def record_payment_success(payment_id, payment_method, duration, amount):
        """Registrar pago exitoso"""
        logger.info(
            "payment_successful",
            payment_id=payment_id,
            payment_method=payment_method,
            duration=duration,
            amount=amount,
        )

        # Incrementar contador de éxito
        cache_key = f"payment_success_{payment_method}"
        success_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, success_count, timeout=86400)  # 24 horas

    @staticmethod
    def record_payment_failure(payment_id, payment_method, error_code, error_message):
        """Registrar fallo de pago"""
        logger.error(
            "payment_failed",
            payment_id=payment_id,
            payment_method=payment_method,
            error_code=error_code,
            error_message=error_message,
        )

        # Incrementar contador de fallos
        cache_key = f"payment_failures_{payment_method}"
        failure_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, failure_count, timeout=86400)  # 24 horas

    @staticmethod
    def get_payment_stats(payment_method):
        """Obtener estadísticas de pagos"""
        success_key = f"payment_success_{payment_method}"
        failure_key = f"payment_failures_{payment_method}"

        success_count = cache.get(success_key, 0)
        failure_count = cache.get(failure_key, 0)
        total_attempts = success_count + failure_count

        success_rate = (
            (success_count / total_attempts * 100) if total_attempts > 0 else 0
        )

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "total_attempts": total_attempts,
            "success_rate": round(success_rate, 2),
        }


class EnhancedPaymentViewSet:
    """Vista mejorada con logging estructurado y métricas"""

    def create_checkout_session_enhanced(self, request):
        """Versión mejorada del método create_checkout_session"""
        start_time = time.time()
        request_id = f"req_{int(start_time)}"

        logger.info(
            "checkout_session_started",
            request_id=request_id,
            user_id=request.user.id,
            data=request.data,
        )

        try:
            # Validar datos de entrada
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            logger.info(
                "checkout_data_validated",
                request_id=request_id,
                validated_data=serializer.validated_data,
            )

            # Obtener carrito
            cart = self.get_user_cart(request.user)
            logger.info(
                "cart_retrieved",
                request_id=request_id,
                cart_id=cart.id,
                items_count=cart.items.count(),
                subtotal=cart.get_subtotal(),
            )

            # Validar método de envío
            shipping = self.validate_checkout_request(
                cart, serializer.validated_data["shipping_id"]
            )
            logger.info(
                "shipping_validated",
                request_id=request_id,
                shipping_id=shipping.id,
                shipping_name=shipping.name,
            )

            # Calcular total
            total = self._calculate_order_total(cart, shipping)
            logger.info(
                "total_calculated",
                request_id=request_id,
                total=total,
                shipping_cost=shipping.calculate_shipping_cost(cart.get_subtotal()),
            )

            # Generar ID de transacción
            transaction_id = self.generate_transaction_id()
            logger.info(
                "transaction_id_generated",
                request_id=request_id,
                transaction_id=transaction_id,
            )

            # Crear orden y pago
            with transaction.atomic():
                order = self.create_order(request.user, total, shipping, transaction_id)
                logger.info(
                    "order_created",
                    request_id=request_id,
                    order_id=order.id,
                    order_amount=order.amount,
                )

                payment = self.create_payment(
                    order,
                    total,
                    serializer.validated_data["payment_method_id"],
                    user=request.user,
                )
                logger.info(
                    "payment_created",
                    request_id=request_id,
                    payment_id=payment.id,
                    payment_amount=payment.amount,
                )

                # Registrar intento de pago
                PaymentMetrics.record_payment_attempt(
                    serializer.validated_data["payment_method_id"], request.user.id
                )

                # Crear sesión de Stripe
                checkout_session = self.create_stripe_session(
                    order, payment, request.user.email
                )
                logger.info(
                    "stripe_session_created",
                    request_id=request_id,
                    session_id=checkout_session.id,
                    checkout_url=checkout_session.url,
                )

                payment.stripe_session_id = checkout_session.id
                payment.save()

            # Calcular duración
            duration = time.time() - start_time

            # Registrar éxito
            PaymentMetrics.record_payment_success(
                payment.id,
                serializer.validated_data["payment_method_id"],
                duration,
                total,
            )

            logger.info(
                "checkout_session_completed",
                request_id=request_id,
                duration=duration,
                payment_id=payment.id,
                session_id=checkout_session.id,
            )

            return Response(
                self.format_checkout_response(checkout_session, payment),
                status=status.HTTP_201_CREATED,
            )

        except ValidationError as e:
            duration = time.time() - start_time
            logger.error(
                "checkout_validation_error",
                request_id=request_id,
                error=str(e),
                duration=duration,
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            duration = time.time() - start_time
            logger.error(
                "stripe_error", request_id=request_id, error=str(e), duration=duration
            )

            # Registrar fallo de pago
            if "payment" in locals():
                PaymentMetrics.record_payment_failure(
                    payment.id,
                    serializer.validated_data.get("payment_method_id", "unknown"),
                    "stripe_error",
                    str(e),
                )

            return Response(
                {"error": "Error al procesar el pago. Por favor, inténtelo de nuevo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "unexpected_error",
                request_id=request_id,
                error=str(e),
                duration=duration,
                exc_info=True,
            )
            return Response(
                {"error": "Error interno del servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_payment_stats_endpoint(self, request):
        """Endpoint para obtener estadísticas de pagos"""
        payment_method = request.query_params.get("payment_method", "all")

        if payment_method == "all":
            # Obtener estadísticas de todos los métodos
            stats = {}
            payment_methods = ["stripe", "paypal"]  # Agregar según tus métodos
            for method in payment_methods:
                stats[method] = PaymentMetrics.get_payment_stats(method)
        else:
            stats = PaymentMetrics.get_payment_stats(payment_method)

        return Response({"payment_stats": stats, "timestamp": time.time()})


# Configuración de structlog para Django
def configure_structlog():
    """Configurar structlog para el proyecto"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
