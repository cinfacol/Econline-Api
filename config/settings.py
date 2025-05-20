from pathlib import Path
from celery.schedules import crontab
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from .logging import LOGGING

import environ

env = environ.Env(DEBUG=(bool, False))

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "0.0.0.0", "[::1]", "192.168.1.4"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    AUTH_COOKIE_SECURE=(bool, False),
    REDIS_HOST=(str, "localhost"),
    REDIS_PORT=(int, 6379),
    REDIS_DB_CELERY=(int, 0),
    REDIS_DB_CACHE=(int, 1),
    REDIS_DB_SESSIONS=(int, 2),
    REDIS_DB_THROTTLING=(int, 3),
)

environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY")

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


DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

PROJECT_APPS = [
    "common.apps.CommonConfig",
    "users.apps.UsersConfig",
    "profiles.apps.ProfilesConfig",
    "reviews.apps.ReviewsConfig",
    "inventory.apps.InventoryConfig",
    "promotion.apps.PromotionConfig",
]

ECOMMERCE_APPS = [
    "products.apps.ProductsConfig",
    "enquiries.apps.EnquiriesConfig",
    "categories.apps.CategoriesConfig",
    "orders.apps.OrdersConfig",
    "cart.apps.CartConfig",
    "shipping.apps.ShippingConfig",
    "payments.apps.PaymentsConfig",
    "coupons.apps.CouponsConfig",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework_api",
    "django_filters",
    "django_countries",
    "phonenumber_field",
    "djoser",
    "social_django",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "djcelery_email",
    "drf_spectacular",
    "cloudinary",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + ECOMMERCE_APPS + THIRD_PARTY_APPS

""" CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "imageUpload",
        ],
    },
} """

SITE_ID = 1

CART_SESSION_ID = "cart"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "users.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = "cinfacol@gmail.com"
DOMAIN = env("DOMAIN")
BACKEND_DOMAIN = env("BACKEND_DOMAIN")
SITE_NAME = env("SITE_NAME")

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:9090",
        "http://127.0.0.1:9090",
        "http://127.0.0.1:3000",
    ],
)

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9090",
    "http://127.0.0.1:9090",
    "http://127.0.0.1:3000",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ADMIN_URL = "supersecret/"

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:9090",
    "http://127.0.0.1:9090",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/staticfiles/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []
MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
]

LOCALE_PATH = BASE_DIR / "locale/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CLOUD_NAME = env("CLOUD_NAME")
API_KEY = env("API_KEY")
API_SECRET = env("API_SECRET")

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # "rest_framework.permissions.IsAuthenticatedOrReadOnly",
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
        "users.authentication.CustomJWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "VirtualEline API",
    "DESCRIPTION": "VirtualEline description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "USERNAME_CHANGED_EMAIL_CONFIRMATION": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "SEND_CONFIRMATION_EMAIL": True,
    # "PASSWORD_RESET_CONFIRM_URL": "password/reset/confirm/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "TOKEN_MODEL": None,
    "USERNAME_RESET_CONFIRM_URL": "email/reset/confirm/{uid}/{token}",
    # "ACTIVATION_URL": "activate/{uid}/{token}",
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
SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = env.list(
    "REDIRECT_URLS",
    default=[
        "http://localhost:3000/auth/google",
        "http://localhost:3000/auth/google/",  # Agregar ambas versiones con y sin slash
        "http://127.0.0.1:3000/auth/google",
        "http://127.0.0.1:3000/auth/google/",
        "http://localhost:3000/auth/facebook",
        "http://localhost:3000/auth/facebook/",
        "http://127.0.0.1:3000/auth/facebook",
        "http://127.0.0.1:3000/auth/facebook/",
        "http://localhost:9090/auth/facebook/callback/",
    ],
)

SOCIAL_AUTH_FACEBOOK_KEY = env("FACEBOOK_AUTH_KEY")
SOCIAL_AUTH_FACEBOOK_SECRET = env("FACEBOOK_AUTH_SECRET_KEY")
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, email, name, picture"}
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
RAISE_EXCEPTIONS = True

# Configuración general de social auth
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

AUTH_COOKIE = "access"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_SECURE = env("AUTH_COOKIE_SECURE")
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = "None"

AUTH_COOKIE = "access"

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": (
        "Bearer",
        "JWT",
    ),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "SIGNING_KEY": env("SIGNING_KEY"),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "VERIFYING_KEY": SECRET_KEY,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "AUTH_COOKIE": AUTH_COOKIE,
    # "AUTH_COOKIE_MAX_AGE": 60 * 60 * 24,
    # "AUTH_COOKIE_SECURE": env("AUTH_COOKIE_SECURE"),
    # "AUTH_COOKIE_HTTP_ONLY": True,
    # "AUTH_COOKIE_PATH": "/",
    # "AUTH_COOKIE_SAMESITE": "Lax" if DEBUG else "Strict",
}


# CELERY_BROKER_URL = env("CELERY_BROKER")
# CELERY_RESULT_BACKEND = env("CELERY_BACKEND")

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY")
PAYMENT_CANCEL_URL = env("PAYMENT_CANCEL_URL")
PAYMENT_SUCCESS_URL = env("PAYMENT_SUCCESS_URL")
BACKEND_DOMAIN = env("BACKEND_DOMAIN")

STRIPE_API_KEY = env("STRIPE_API_KEY")
FRONTEND_URL = env("FRONTEND_URL")
FRONTEND_STORE_URL = env("FRONTEND_STORE_URL")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")

BT_ENVIRONMENT = env("BT_ENVIRONMENT")
BT_MERCHANT_ID = env("BT_MERCHANT_ID")
BT_PUBLIC_KEY = env("BT_PUBLIC_KEY")
BT_PRIVATE_KEY = env("BT_PRIVATE_KEY")

# Configuración de Seguridad
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Configuración de Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
RATELIMIT_FAIL_OPEN = False
RATELIMIT_IP_META_KEY = "HTTP_X_FORWARDED_FOR"

# Lista blanca de IPs (opcional)
RATELIMIT_WHITELIST = ["127.0.0.1", "172.18.0.1"]

# Redis Configuration
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_DB_CELERY = env("REDIS_DB_CELERY", default=0)
REDIS_DB_CACHE = env("REDIS_DB_CACHE", default=1)
REDIS_DB_SESSIONS = env("REDIS_DB_SESSIONS", default=2)
REDIS_DB_THROTTLING = env("REDIS_DB_THROTTLING", default=3)

# Celery Configuration
CELERY_BROKER_URL = env(
    "CELERY_BROKER", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}"
)
CELERY_RESULT_BACKEND = env(
    "CELERY_BACKEND", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CELERY}"
)
CELERY_TIMEZONE = "America/Bogota"

CELERY_BEAT_SCHEDULE = {
    "sample_task": {
        "task": "ecommerce.promotion.promotion_management",
        "schedule": crontab(minute="0", hour="1"),
    },
}

# Configuración de Celery
# CELERY_BROKER_URL = f"redis://redis:6379/{REDIS_DB_CELERY}"
# CELERY_RESULT_BACKEND = f"redis://redis:6379/{REDIS_DB_CELERY}"

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Bogota"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

# Configuración de Redis Broker
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 3600,  # 1 hora
    "socket_timeout": 30,
    "socket_connect_timeout": 30,
    "socket_keepalive": True,
}

# Configuración de resultados
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # 24 horas
CELERY_RESULT_EXTENDED = True

# Cache Configuration
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

# Session Configuration (opcional, si usas sesiones basadas en cache)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

# Configuración de intentos de login
MAX_LOGIN_ATTEMPTS = env.int(
    "MAX_LOGIN_ATTEMPTS", default=5
)  # número máximo de intentos
LOGIN_ATTEMPT_TIMEOUT = env.int(
    "LOGIN_ATTEMPT_TIMEOUT", default=300
)  # tiempo de bloqueo en segundos (5 minutos)

# Configuración adicional de seguridad recomendada
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = MAX_LOGIN_ATTEMPTS
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = LOGIN_ATTEMPT_TIMEOUT
