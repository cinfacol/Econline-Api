from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden
from .utils import SecurityUtils
import logging
import re

logger = logging.getLogger("security")


class SecurityHeadersMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        # Definir CSP whitelist con valores por defecto
        self.csp_whitelist = [
            "'self'",
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com",
            "http://localhost:9090",
            "http://127.0.0.1:9090",
        ]

        self.admin_paths = [
            "/supersecret/",
            "/supersecret/auth/login/",
            "/supersecret/auth/logout/",
        ]

        # Obtener configuración adicional de settings si existe
        if hasattr(settings, "CSP_WHITELIST"):
            self.csp_whitelist.extend(settings.CSP_WHITELIST)

    def process_request(self, request):
        """Procesa la petición antes de que llegue a la vista"""
        # Obtener IP del cliente
        ip = SecurityUtils.get_client_ip(request)

        # No aplicar verificaciones para rutas API
        if request.path.startswith("/api/"):
            request.client_ip = ip
            return None

        # Verificar origen de la petición
        origin = request.headers.get("Origin", "")
        if origin and origin not in settings.CORS_ALLOWED_ORIGINS:
            logger.warning(f"Origen no permitido detectado: {origin} desde IP: {ip}")
            return HttpResponseForbidden("Forbidden - Origin not allowed")

        # Verificar si la petición es sospechosa
        if SecurityUtils.is_suspicious_request(request):
            logger.warning(
                f"Petición bloqueada - Patrón sospechoso detectado desde IP: {ip}"
            )
            return HttpResponseForbidden("Forbidden - Suspicious request detected")

        # Agregar IP a request para uso posterior
        request.client_ip = ip

        logger.debug(f"Petición recibida desde IP: {ip} - Path: {request.path}")

    def process_response(self, request, response):
        # Obtener IP (ya sea de request o usando SecurityUtils)
        ip = getattr(request, "client_ip", SecurityUtils.get_client_ip(request))

        # Security Headers Básicos
        response["X-XSS-Protection"] = "1; mode=block"
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (anteriormente Feature-Policy)
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # CORS headers en desarrollo
        if settings.DEBUG:
            origin = request.headers.get("Origin", "")
            if origin in settings.CORS_ALLOWED_ORIGINS:
                response["Access-Control-Allow-Origin"] = origin
                response["Access-Control-Allow-Credentials"] = "true"
                response["Access-Control-Allow-Methods"] = (
                    "GET, POST, OPTIONS, PUT, DELETE, PATCH"
                )
                response["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-CSRFToken"
                )

        # Content Security Policy Dinámico
        csp_directives = [
            f"default-src {' '.join(self.csp_whitelist)}",
            "img-src 'self' data: https:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS
        if settings.SECURE_SSL_REDIRECT:
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # HSTS en producción
        if not settings.DEBUG:
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Agregar header personalizado con IP (opcional, solo para debugging)
        if settings.DEBUG:
            response["X-Client-IP"] = ip

        # Logging de respuesta
        status_code = response.status_code
        if status_code >= 400:
            logger.warning(
                f"Respuesta con error {status_code} enviada a IP: {ip} - Path: {request.path}"
            )
        else:
            logger.debug(
                f"Respuesta exitosa {status_code} enviada a IP: {ip} - Path: {request.path}"
            )

        # CORS headers para API
        if request.path.startswith("/api/"):
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS, PUT, DELETE, PATCH"
            )
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

            # Si es una petición OPTIONS, retornar 200
            if request.method == "OPTIONS":
                response.status_code = 200

        return response

    def process_exception(self, request, exception):
        """Maneja excepciones no capturadas"""
        ip = getattr(request, "client_ip", SecurityUtils.get_client_ip(request))

        logger.error(
            f"Excepción no manejada para IP: {ip} - Path: {request.path} - Error: {str(exception)}",
            exc_info=True,
        )

        return None  # Permite que Django maneje la excepción normalmente
