from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from .utils import SecurityUtils
import logging

logger = logging.getLogger("security")

logger.info("Mensaje informativo")
logger.warning("Mensaje de advertencia")
logger.error("Mensaje de error")
logger.critical("Mensaje crítico")


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            # Obtener IP y verificar petición sospechosa
            ip = SecurityUtils.get_client_ip(request)

            if SecurityUtils.is_suspicious_request(request):
                logger.warning(f"Intento de autenticación sospechoso desde IP: {ip}")
                return None

            # Obtener token
            header = self.get_header(request)
            if header is None:
                raw_token = request.COOKIES.get(settings.AUTH_COOKIE)
                logger.debug(f"Token obtenido de cookies para IP: {ip}")
            else:
                raw_token = self.get_raw_token(header)
                logger.debug(f"Token obtenido de header para IP: {ip}")

            if raw_token is None:
                logger.debug(f"No se encontró token para IP: {ip}")
                return None

            # Validar token
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)

            # Log de autenticación exitosa
            logger.info(
                f"Autenticación exitosa para usuario: {user.email} desde IP: {ip}"
            )

            # Resetear intentos fallidos si existen
            SecurityUtils.track_failed_attempts(ip, increment=False)

            return user, validated_token

        except Exception as e:
            ip = SecurityUtils.get_client_ip(request)
            logger.warning(
                f"Error de autenticación desde IP: {ip} - Error: {str(e)}",
                exc_info=True,
            )

            # Incrementar contador de intentos fallidos
            SecurityUtils.track_failed_attempts(ip, increment=True)

            return None

    def authenticate_header(self, request):
        return "Bearer"
