from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.middleware import csrf
from djoser.social.views import ProviderAuthView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.core.cache import caches
from .utils import RedisUtils
from datetime import datetime
from .utils import SecurityUtils
import logging

from users.serializers import CustomTokenObtainPairSerializer
from users.throttling import LoginRateThrottle

logger = logging.getLogger("security")

logger.info("Mensaje informativo")
logger.warning("Mensaje de advertencia")
logger.error("Mensaje de error")
logger.critical("Mensaje crítico")

User = get_user_model()


class CookieMixin:
    """Mixin para manejar cookies de manera consistente"""

    def set_auth_cookies(self, response, access=None, refresh=None):
        try:
            if access:
                response.set_cookie(
                    "access",
                    access,
                    max_age=settings.SIMPLE_JWT[
                        "ACCESS_TOKEN_LIFETIME"
                    ].total_seconds(),
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
                )

            if refresh:
                response.set_cookie(
                    "refresh",
                    refresh,
                    max_age=settings.SIMPLE_JWT[
                        "REFRESH_TOKEN_LIFETIME"
                    ].total_seconds(),
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
                )

            # Establecer CSRF token
            csrf.get_token(self.request)

        except Exception as e:
            logger.error(f"Error setting auth cookies: {str(e)}")
            raise ValidationError("Error setting authentication cookies")


class CustomProviderAuthView(CookieMixin, ProviderAuthView):
    def post(self, request, *args, **kwargs):
        try:
            # Log de datos recibidos (sin la contraseña)
            logger.debug(f"Login attempt for email: {request.data.get('email')}")
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Obtener los tokens de la respuesta
                access_token = response.data.get("access")
                refresh_token = response.data.get("refresh")

                self.set_auth_cookies(
                    response,
                    access=response.data.get("access"),
                    refresh=response.data.get("refresh"),
                )
                # Limpiar tokens de la respuesta
                response.data = {"detail": "Authentication successful"}

            return response
        except Exception as e:
            logger.warning(f"Token error during login: {str(e)}")
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenObtainPairView(CookieMixin, TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Obtener IP y email
        ip = SecurityUtils.get_client_ip(request)
        email = request.data.get("email", "")

        # Usar la caché específica para throttling
        throttling_cache = RedisUtils.get_throttling_cache()

        # Verificar si la petición es sospechosa
        if SecurityUtils.is_suspicious_request(request):
            logger.warning(f"Petición sospechosa detectada desde IP: {ip}")
            return Response(
                {"status": "error", "message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar si la IP está en la lista negra
        if SecurityUtils.is_blacklisted(ip):
            logger.warning(f"Intento de login bloqueado para IP en lista negra: {ip}")
            return Response(
                {
                    "status": "error",
                    "message": "Access denied",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Verificar intentos fallidos usando SecurityUtils
            failed_attempts = SecurityUtils.track_failed_attempts(ip, increment=False)
            if failed_attempts and failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                logger.warning(f"Demasiados intentos fallidos desde IP: {ip}")
                return Response(
                    {
                        "status": "error",
                        "message": "Too many failed attempts. Please try again later.",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Login exitoso - resetear contadores y limpiar cachés
                SecurityUtils.track_failed_attempts(ip, increment=False)
                RedisUtils.clear_ip_throttling(ip)

                # Si el usuario existe, limpiar su caché
                user = User.objects.filter(email=email).first()
                if user:
                    RedisUtils.clear_user_cache(user.id)

                # Establecer cookies y procesar respuesta
                access_token = response.data.get("access")
                refresh_token = response.data.get("refresh")

                self.set_auth_cookies(response, access_token, refresh_token)

                # Log de login exitoso
                logger.info(f"Login exitoso para usuario: {email} desde IP: {ip}")

                response.data = {"status": "success", "message": "Login successful"}

            return response

        except Exception as e:
            # Incrementar contador de intentos fallidos usando SecurityUtils
            SecurityUtils.track_failed_attempts(ip, increment=True)

            # Log del error
            logger.error(
                f"Error de login para usuario: {email} desde IP: {ip}. Error: {str(e)}"
            )

            return Response(
                {"status": "error", "message": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomTokenRefreshView(CookieMixin, TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            # Obtener refresh token de las cookies
            refresh_token = request.COOKIES.get("refresh")
            if not refresh_token:
                return Response(
                    {"message": "No refresh token found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear el payload
            request.data["refresh"] = refresh_token

            # Obtener nuevo access token
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Establecer nueva cookie de acceso
                response.set_cookie(
                    settings.AUTH_COOKIE,
                    response.data.get("access"),
                    max_age=settings.SIMPLE_JWT[
                        "ACCESS_TOKEN_LIFETIME"
                    ].total_seconds(),
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
                )

                # Modificar la respuesta
                response.data = {
                    "status": "success",
                    "message": "Token refreshed successfully",
                }

            return response

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return Response(
                {"status": "error", "message": "Failed to refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        try:
            access_token = request.COOKIES.get("access")
            if not access_token:
                raise TokenError("No access token found")

            request.data["token"] = access_token
            response = super().post(request, *args, **kwargs)

            return Response({"detail": "Token is valid"})
        except TokenError:
            return Response(
                {"detail": "Token is invalid or expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return Response(
                {"detail": "Token verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # Obtener IP y usuario antes de logout
            ip = SecurityUtils.get_client_ip(request)
            user_id = request.user.id if request.user.is_authenticated else None

            # Limpiar cachés relacionadas
            if user_id:
                RedisUtils.clear_user_cache(user_id)
            RedisUtils.clear_ip_throttling(ip)

            # Crear respuesta
            response = Response(
                {"status": "success", "message": "Logged out successfully"},
                status=status.HTTP_200_OK,
            )

            # Eliminar cookies
            for cookie in [settings.AUTH_COOKIE, "refresh"]:
                response.delete_cookie(
                    cookie,
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
                    domain=settings.SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None),
                )

            # Log con información adicional
            logger.info(
                f"Logout exitoso - IP: {ip} {'- Usuario: ' + str(user_id) if user_id else ''}"
            )

            return response
        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            return Response(
                {"status": "error", "message": "Error processing logout"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AuthStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            return Response(
                {
                    "status": "success",
                    "authenticated": True,
                    "user": {
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_staff": user.is_staff,
                        "last_login": user.last_login,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Error checking auth status: {str(e)}")
            return Response(
                {"status": "error", "message": "Error checking authentication status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
