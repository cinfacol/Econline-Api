"""
Configuraciones específicas para el entorno de desarrollo
"""

from .base import *
from config.logging import LOGGING, setup_payment_logging

# Setup logging
setup_payment_logging()
LOGGING = LOGGING

# Leer variables de entorno
environ.Env.read_env(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=True)

# Allowed hosts para desarrollo
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "[::1]",
        "192.168.1.4",
        "localhost:9090",
    ],
)

# Database para desarrollo
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD", default=""),
        "HOST": env("PG_HOST", default="localhost"),
        "PORT": env("PG_PORT", default="5432"),
    }
}

# Email backend para desarrollo (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")

# CORS settings para desarrollo
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:9090",
        "http://127.0.0.1:9090",
        "http://127.0.0.1:3000",
    ],
)

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9090",
    "http://127.0.0.1:9090",
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:9090",
    "http://127.0.0.1:9090",
]

# Security settings para desarrollo
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
AUTH_COOKIE_SECURE = env("AUTH_COOKIE_SECURE", default=False)

# Redis Configuration para desarrollo
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_DB_CELERY = env("REDIS_DB_CELERY", default=0)
REDIS_DB_CACHE = env("REDIS_DB_CACHE", default=1)
REDIS_DB_SESSIONS = env("REDIS_DB_SESSIONS", default=2)
REDIS_DB_THROTTLING = env("REDIS_DB_THROTTLING", default=3)

# Celery Configuration para desarrollo
CELERY_BROKER_URL = env(
    "CELERY_BROKER", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}"
)
CELERY_RESULT_BACKEND = env(
    "CELERY_BACKEND", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}"
)

# Cache Configuration para desarrollo
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CACHE}",
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 50,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        },
    },
    "throttling": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_THROTTLING}",
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 20,
        },
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_SESSIONS}",
        "OPTIONS": {
            "retry_on_timeout": True,
            "max_connections": 20,
        },
    },
}

# Channel layers para desarrollo
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# Admin URL para desarrollo
ADMIN_URL = "admin/"

# Simple JWT para desarrollo
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
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
    "AUTH_COOKIE_MAX_AGE": 60 * 60 * 24,
    "AUTH_COOKIE_SECURE": False,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_SAMESITE": "Lax",
}

# Cloudinary para desarrollo
CLOUD_NAME = env("CLOUD_NAME", default="")
API_KEY = env("API_KEY", default="")
API_SECRET = env("API_SECRET", default="")

# Djoser configuration para desarrollo
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
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": env.list(
        "REDIRECT_URLS",
        default=[
            "http://localhost:3000/auth/google",
            "http://localhost:3000/auth/facebook",
        ],
    ),
    "SERIALIZERS": {
        "user_create": "users.serializers.CreateUserSerializer",
        "user": "users.serializers.UserSerializer",
        "current_user": "users.serializers.UserSerializer",
        "user_delete": "djoser.serializers.UserDeleteSerializer",
    },
}

# Social Auth para desarrollo
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env("GOOGLE_AUTH_KEY", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env("GOOGLE_AUTH_SECRET_KEY", default="")
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

SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = env.list(
    "REDIRECT_URLS",
    default=[
        "http://localhost:3000/auth/google",
        "http://localhost:3000/auth/google/",
        "http://127.0.0.1:3000/auth/google",
        "http://127.0.0.1:3000/auth/google/",
        "http://localhost:3000/auth/facebook",
        "http://localhost:3000/auth/facebook/",
        "http://127.0.0.1:3000/auth/facebook",
        "http://127.0.0.1:3000/auth/facebook/",
        "http://localhost:9090/auth/facebook/callback/",
    ],
)

SOCIAL_AUTH_FACEBOOK_KEY = env("FACEBOOK_AUTH_KEY", default="")
SOCIAL_AUTH_FACEBOOK_SECRET = env("FACEBOOK_AUTH_SECRET_KEY", default="")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, email, name, picture"}
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
RAISE_EXCEPTIONS = True

# Payment settings para desarrollo
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_API_KEY = env("STRIPE_API_KEY", default="")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
FRONTEND_STORE_URL = env("FRONTEND_STORE_URL", default="http://localhost:3000")

PAYMENT_SUCCESS_URL = env(
    "PAYMENT_SUCCESS_URL", default="http://localhost:3000/payment/success"
)
PAYMENT_CANCEL_URL = env(
    "PAYMENT_CANCEL_URL", default="http://localhost:3000/payment/cancel"
)

PAYMENT_EMAIL_FROM = env("PAYMENT_EMAIL_FROM", default="noreply@localhost")

# Braintree para desarrollo
BT_ENVIRONMENT = env("BT_ENVIRONMENT", default="sandbox")
BT_MERCHANT_ID = env("BT_MERCHANT_ID", default="")
BT_PUBLIC_KEY = env("BT_PUBLIC_KEY", default="")
BT_PRIVATE_KEY = env("BT_PRIVATE_KEY", default="")

# Servientrega para desarrollo
SERVIENTREGA_API_KEY = env("SERVIENTREGA_API_KEY", default="")
SERVIENTREGA_USERNAME = env("SERVIENTREGA_USERNAME", default="")
SERVIENTREGA_PASSWORD = env("SERVIENTREGA_PASSWORD", default="")
SERVIENTREGA_ORIGIN_CODE = env("SERVIENTREGA_ORIGIN_CODE", default="")

# Domain settings para desarrollo
DOMAIN = env("DOMAIN", default="http://localhost:3000")
BACKEND_DOMAIN = env("BACKEND_DOMAIN", default="http://localhost:9090")
SITE_NAME = env("SITE_NAME", default="Econline Development")

# Override configuraciones específicas para desarrollo
AUTH_COOKIE = "access"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = "Lax"

# Configuraciones de seguridad relajadas para desarrollo
SECURE_PROXY_SSL_HEADER = None
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# No usar HSTS en desarrollo
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Rate limiting más relajado para desarrollo
RATELIMIT_WHITELIST = ["127.0.0.1", "172.18.0.1", "localhost"]
