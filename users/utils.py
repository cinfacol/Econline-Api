import re
from typing import Optional
from django.core.cache import caches
from django.conf import settings
import logging

logger = logging.getLogger("security")


class RedisUtils:
    @staticmethod
    def get_throttling_cache():
        return caches["throttling"]

    @staticmethod
    def get_default_cache():
        return caches["default"]

    @staticmethod
    def get_sessions_cache():
        return caches["sessions"]

    @staticmethod
    def clear_user_cache(user_id: int) -> None:
        """Limpia todas las cachés relacionadas con un usuario"""
        default_cache = RedisUtils.get_default_cache()
        throttling_cache = RedisUtils.get_throttling_cache()

        # Limpiar cachés específicas del usuario
        default_cache.delete(f"user_{user_id}_profile")
        throttling_cache.delete(f"throttle_user_{user_id}")

    @staticmethod
    def clear_ip_throttling(ip: str) -> None:
        """Limpia el throttling para una IP específica"""
        throttling_cache = RedisUtils.get_throttling_cache()
        throttling_cache.delete(f"throttle_anon_{ip}")


class SecurityUtils:
    throttling_cache = caches["throttling"]

    # Lista de rutas administrativas permitidas
    ADMIN_PATHS = [
        "/supersecret/",
        "/supersecret/login/",
        "/supersecret/logout/",
        "/admin/",
        "/admin/login/",
        "/admin/logout/",
    ]

    # Lista de rutas de API permitidas
    API_PATHS = [
        "/api/auth/jwt/create",
        "/api/auth/jwt/refresh",
        "/api/auth/jwt/verify",
        "/api/auth/users/me",
        "/api/auth/users/",
    ]

    # Lista de referers administrativos permitidos
    ADMIN_REFERERS = [
        "http://localhost:9090/supersecret/",
        "http://127.0.0.1:9090/supersecret/",
    ]

    @staticmethod
    def get_client_ip(request) -> str:
        """Obtiene la IP real del cliente incluso detrás de proxies"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    @staticmethod
    def is_suspicious_request(request) -> bool:
        """Detecta patrones sospechosos en las peticiones"""
        path = request.path.rstrip("/")  # Eliminar slash final para comparación

        # Si la ruta está en las permitidas, no es sospechosa
        if path in SecurityUtils.ADMIN_PATHS or path in SecurityUtils.API_PATHS:
            return False

        # Si es una ruta de API, permitir
        if path.startswith("/api/"):
            for api_path in SecurityUtils.API_PATHS:
                if path.startswith(api_path):
                    return False

        # Verificar el origen de la petición
        origin = request.headers.get("Origin", "")
        referer = request.headers.get("Referer", "")

        # Lista de orígenes permitidos
        allowed_origins = getattr(
            settings,
            "CORS_ALLOWED_ORIGINS",
            [
                "http://localhost:9090",
                "http://127.0.0.1:9090",
            ],
        )

        # Si el origen está en la lista de permitidos, no es sospechoso
        if origin and origin in allowed_origins:
            return False

        # Verificar referer para rutas admin
        if referer and any(
            referer.startswith(ref) for ref in SecurityUtils.ADMIN_REFERERS
        ):
            return False

        # Patrones sospechosos a verificar
        suspicious_patterns = [
            r"..//",  # Path traversal
            r"SELECT.*FROM",  # SQL injection
            r"<script",  # XSS
            r"javascript:",  # XSS
            r"eval\(",  # JavaScript eval
            r"document\.cookie",  # Cookie stealing
            r"onload=",  # XSS events
            r"onerror=",  # XSS events
            r"UNION.*SELECT",  # SQL injection
            r"DROP.*TABLE",  # SQL injection
        ]

        # Verificar headers y parámetros
        headers_to_check = [
            request.headers.get("User-Agent", ""),
            origin if origin not in allowed_origins else "",
            (
                referer
                if not any(
                    referer.startswith(ref) for ref in SecurityUtils.ADMIN_REFERERS
                )
                else ""
            ),
        ]

        # Verificar headers
        for key, value in request.headers.items():
            for pattern in suspicious_patterns:
                if re.search(pattern, str(value), re.I):
                    logger.warning(
                        f"Patrón sospechoso detectado en header {key} desde IP: {SecurityUtils.get_client_ip(request)}"
                    )
                    return True

        # Verificar parámetros POST
        for key, value in request.POST.items():
            for pattern in suspicious_patterns:
                if re.search(pattern, str(value), re.I):
                    logger.warning(
                        f"Patrón sospechoso detectado en POST {key} desde IP: {SecurityUtils.get_client_ip(request)}"
                    )
                    return True

        # Verificar parámetros GET
        for key, value in request.GET.items():
            for pattern in suspicious_patterns:
                if re.search(pattern, str(value), re.I):
                    logger.warning(
                        f"Patrón sospechoso detectado en GET {key} desde IP: {SecurityUtils.get_client_ip(request)}"
                    )
                    return True

        return False

    @staticmethod
    def track_failed_attempts(ip: str, increment: bool = True) -> Optional[int]:
        """Rastrea intentos fallidos de login"""
        cache_key = f"failed_attempts:{ip}"
        throttling_cache = caches["throttling"]
        attempts = throttling_cache.get(cache_key, 0)

        if increment:
            attempts += 1
            throttling_cache.set(cache_key, attempts, timeout=3600)  # 1 hora

            # Log del incremento de intentos fallidos
            logger.warning(f"Intento fallido #{attempts} desde IP: {ip}")

            # Si se alcanza el límite, agregar a la lista negra
            if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                SecurityUtils.add_to_blacklist(ip)
                logger.critical(
                    f"IP {ip} agregada a la lista negra después de {attempts} intentos fallidos"
                )

        return attempts

    @staticmethod
    def add_to_blacklist(ip: str, duration: int = 86400) -> None:
        """Agrega una IP a la lista negra"""
        throttling_cache = caches["throttling"]
        key = f"blacklist_{ip}"
        throttling_cache.set(key, True, duration)  # Por defecto 24 horas
        logger.warning(f"IP {ip} agregada a la lista negra por {duration} segundos")

    @staticmethod
    def is_blacklisted(ip: str) -> bool:
        """Verifica si una IP está en la lista negra"""
        throttling_cache = caches["throttling"]
        return throttling_cache.get(f"blacklist_{ip}", False)

    @staticmethod
    def remove_from_blacklist(ip: str) -> None:
        """Elimina una IP de la lista negra"""
        throttling_cache = caches["throttling"]
        throttling_cache.delete(f"blacklist_{ip}")
        logger.info(f"IP {ip} removida de la lista negra")
