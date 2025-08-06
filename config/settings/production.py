"""
Configuraciones específicas para el entorno de producción
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import logging.config

# Leer variables de entorno
environ.Env.read_env(BASE_DIR / ".env.production")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts para producción
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[],  # Debe ser definido en .env.production
)

# Database para producción
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("PG_HOST"),
        "PORT": env("PG_PORT", default="5432"),
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# Email backend para producción
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
CELERY_EMAIL_BACKEND = env(
    "CELERY_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = env("EMAIL_HOST")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# CORS settings para producción
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

CORS_ORIGIN_WHITELIST = env.list("CORS_ALLOWED_ORIGINS")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

# Security settings para producción
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_COOKIE_SECURE = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS Security
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Additional security headers
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Redis Configuration para producción
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_PASSWORD = env("REDIS_PASSWORD", default=None)
REDIS_DB_CELERY = env("REDIS_DB_CELERY", default=0)
REDIS_DB_CACHE = env("REDIS_DB_CACHE", default=1)
REDIS_DB_SESSIONS = env("REDIS_DB_SESSIONS", default=2)
REDIS_DB_THROTTLING = env("REDIS_DB_THROTTLING", default=3)


# Construir URL de Redis con autenticación si es necesario
def build_redis_url(db):
    if REDIS_PASSWORD:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{db}"
    return f"redis://{REDIS_HOST}:{REDIS_PORT}/{db}"


# Celery Configuration para producción
CELERY_BROKER_URL = env("CELERY_BROKER", default=build_redis_url(REDIS_DB_CELERY))
CELERY_RESULT_BACKEND = env("CELERY_BACKEND", default=build_redis_url(REDIS_DB_CELERY))

# Cache Configuration para producción
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": build_redis_url(REDIS_DB_CACHE),
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 100,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "connection_pool_kwargs": {
                "max_connections": 100,
                "retry_on_timeout": True,
            },
        },
        "TIMEOUT": 300,
        "KEY_PREFIX": "econline_cache",
    },
    "throttling": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": build_redis_url(REDIS_DB_THROTTLING),
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 50,
        },
        "TIMEOUT": 3600,
        "KEY_PREFIX": "econline_throttle",
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": build_redis_url(REDIS_DB_SESSIONS),
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 50,
        },
        "TIMEOUT": 86400,  # 24 horas
        "KEY_PREFIX": "econline_session",
    },
}

# Channel layers para producción
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [build_redis_url(0)],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# Admin URL para producción (secreto)
ADMIN_URL = env("ADMIN_URL", default="supersecret/")

# Simple JWT para producción
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),  # Más corto en producción
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=24),
    "SIGNING_KEY": env("SIGNING_KEY"),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "VERIFYING_KEY": SECRET_KEY,
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "AUTH_COOKIE": "access",
    "AUTH_COOKIE_MAX_AGE": 60 * 15,  # 15 minutos
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Strict",
}

# Cloudinary para producción
CLOUD_NAME = env("CLOUD_NAME")
API_KEY = env("API_KEY")
API_SECRET = env("API_SECRET")

# Djoser configuration para producción
DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "USERNAME_CHANGED_EMAIL_CONFIRMATION": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "TOKEN_MODEL": None,
    "USERNAME_RESET_CONFIRM_URL": "email/reset/confirm/{uid}/{token}",
    "ACTIVATION_URL": "activation/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": True,
    "SOCIAL_AUTH_TOKEN_STRATEGY": "djoser.social.token.jwt.TokenStrategy",
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": env.list("REDIRECT_URLS"),
    "SERIALIZERS": {
        "user_create": "users.serializers.CreateUserSerializer",
        "user": "users.serializers.UserSerializer",
        "current_user": "users.serializers.UserSerializer",
        "user_delete": "djoser.serializers.UserDeleteSerializer",
    },
}

# Social Auth para producción
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_AUTH_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_AUTH_SECRET_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["username", "first_name", "last_name"]
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    "access_type": "offline",
    "prompt": "consent",
}

SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = env.list("REDIRECT_URLS")

SOCIAL_AUTH_FACEBOOK_KEY = env("FACEBOOK_AUTH_KEY")
SOCIAL_AUTH_FACEBOOK_SECRET = env("FACEBOOK_AUTH_SECRET_KEY")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, email, name, picture"}
SOCIAL_AUTH_RAISE_EXCEPTIONS = False  # No mostrar errores en producción
RAISE_EXCEPTIONS = False

# Payment settings para producción
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")
STRIPE_API_KEY = env("STRIPE_API_KEY")

FRONTEND_URL = env("FRONTEND_URL")
FRONTEND_STORE_URL = env("FRONTEND_STORE_URL")

PAYMENT_SUCCESS_URL = env("PAYMENT_SUCCESS_URL")
PAYMENT_CANCEL_URL = env("PAYMENT_CANCEL_URL")

PAYMENT_EMAIL_FROM = env("PAYMENT_EMAIL_FROM")

# Braintree para producción
BT_ENVIRONMENT = env("BT_ENVIRONMENT", default="production")
BT_MERCHANT_ID = env("BT_MERCHANT_ID")
BT_PUBLIC_KEY = env("BT_PUBLIC_KEY")
BT_PRIVATE_KEY = env("BT_PRIVATE_KEY")

# Servientrega para producción
SERVIENTREGA_API_KEY = env("SERVIENTREGA_API_KEY")
SERVIENTREGA_USERNAME = env("SERVIENTREGA_USERNAME")
SERVIENTREGA_PASSWORD = env("SERVIENTREGA_PASSWORD")
SERVIENTREGA_ORIGIN_CODE = env("SERVIENTREGA_ORIGIN_CODE")

# Domain settings para producción
DOMAIN = env("DOMAIN")
BACKEND_DOMAIN = env("BACKEND_DOMAIN")
SITE_NAME = env("SITE_NAME")

# Override configuraciones específicas para producción
AUTH_COOKIE = "access"
AUTH_COOKIE_MAX_AGE = 60 * 15  # 15 minutos
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = "Strict"

# Rate limiting más estricto para producción
MAX_LOGIN_ATTEMPTS = env.int("MAX_LOGIN_ATTEMPTS", default=3)
LOGIN_ATTEMPT_TIMEOUT = env.int("LOGIN_ATTEMPT_TIMEOUT", default=600)  # 10 minutos

RATELIMIT_WHITELIST = []  # Sin whitelist en producción

# Logging configuration para producción
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"level":"%(levelname)s","time":"%(asctime)s","module":"%(module)s","message":"%(message)s"}',
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/econline/django.log",
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/econline/error.log",
            "maxBytes": 1024 * 1024 * 50,  # 50 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "security_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/econline/security.log",
            "maxBytes": 1024 * 1024 * 25,  # 25 MB
            "backupCount": 10,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.security": {
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": True,
        },
        "celery": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "payments": {
            "handlers": ["file", "error_file"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "INFO",
    },
}

# Sentry configuration para monitoreo de errores
SENTRY_DSN = env("SENTRY_DSN", default=None)

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
                signals_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
        ],
        traces_sample_rate=0.1,  # Capturar 10% de las transacciones para performance
        send_default_pii=False,  # No enviar información personal
        environment="production",
        release=env("GIT_COMMIT", default="unknown"),
        before_send=lambda event, hint: event if event.get("level") != "info" else None,
    )

# Performance optimizations
# Connection pooling
DATABASES["default"]["OPTIONS"].update(
    {
        "MAX_CONNS": 20,
        "MIN_CONNS": 5,
    }
)

# Media files configuration para producción
if env("USE_S3", default=False):
    # Si usas S3 para media files
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }

    # Static and media files
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# Configuración de monitoreo de salud
HEALTH_CHECK_URL = "/health/"

# Configuraciones adicionales de seguridad
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Configuración de timeouts
CONN_HEALTH_CHECKS = True
