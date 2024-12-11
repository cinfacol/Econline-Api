from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import caches
from django.conf import settings
from .utils import SecurityUtils
import logging

logger = logging.getLogger("security")


class CustomRateThrottleMixin:
    cache = caches["throttling"]  # Usar la caché específica para throttling

    def get_cache_key(self, request, view):
        """Obtiene una clave de caché única basada en IP y User-Agent"""
        ip = SecurityUtils.get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:256]
        return f"{self.scope}_{ip}_{user_agent}"

    def get_rate(self):
        """Ajusta el rate según el historial de la IP"""
        ip = SecurityUtils.get_client_ip(self.request)
        failed_attempts = SecurityUtils.track_failed_attempts(ip, increment=False)

        if failed_attempts and failed_attempts >= settings.MAX_LOGIN_ATTEMPTS // 2:
            # Reducir el rate a la mitad si hay muchos intentos fallidos
            return "2/minute"
        return self.rate


class LoginRateThrottle(CustomRateThrottleMixin, AnonRateThrottle):
    scope = "login"
    rate = "5/minute"
    cache = caches["throttling"]

    # Lista blanca de IPs
    WHITELISTED_IPS = ["172.18.0.7"]

    def __init__(self):
        super().__init__()
        self.history = []

    def allow_request(self, request, view):
        ip_current = request.META.get("REMOTE_ADDR")
        logger.info(f"IP de la solicitud: {ip_current}")

        # Verificar si la IP está en la lista blanca
        if ip_current in self.WHITELISTED_IPS:
            return True

        ip = SecurityUtils.get_client_ip(request)

        # Verificar si la petición es sospechosa
        if SecurityUtils.is_suspicious_request(request):
            logger.warning(
                f"Petición sospechosa bloqueada por throttling desde IP: {ip}"
            )
            return False

        # Verificar si la IP está en la lista negra
        if self.is_blacklisted(ip):
            logger.warning(f"IP bloqueada por throttling: {ip}")
            return False

        allowed = super().allow_request(request, view)

        if not allowed:
            logger.warning(f"Rate limit excedido para IP: {ip}")
            self.increment_blocked_attempts(ip)

        return allowed

    def is_blacklisted(self, ip):
        """Verifica si una IP está en la lista negra"""
        key = f"blacklist_{ip}"
        return self.cache.get(key, False)

    def increment_blocked_attempts(self, ip):
        """Incrementa el contador de intentos bloqueados"""
        key = f"blocked_attempts_{ip}"
        attempts = self.cache.get(key, 0) + 1

        if attempts >= 10:  # Si hay más de 10 intentos bloqueados
            # Agregar a la lista negra por 24 horas
            self.cache.set(f"blacklist_{ip}", True, 86400)
            logger.warning(f"IP agregada a la lista negra: {ip}")

        self.cache.set(key, attempts, 3600)  # Expira en 1 hora


class UserLoginRateThrottle(CustomRateThrottleMixin, UserRateThrottle):
    scope = "user_login"
    rate = "20/minute"
    cache = caches["throttling"]  # Asegurar que esta clase use la caché de throttling

    def allow_request(self, request, view):
        if request.user.is_staff:
            return True

        allowed = super().allow_request(request, view)

        if not allowed:
            ip = SecurityUtils.get_client_ip(request)
            logger.warning(
                f"Rate limit excedido para usuario autenticado: {request.user.email} desde IP: {ip}"
            )

        return allowed

    def get_cache_key(self, request, view):
        """Personalizar la clave de caché para usuarios autenticados"""
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
