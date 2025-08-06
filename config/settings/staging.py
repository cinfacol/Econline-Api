"""
Configuraciones específicas para el entorno de staging/testing
"""

from .production import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

# Leer variables de entorno específicas de staging
environ.Env.read_env(BASE_DIR / ".env.staging")

# Allowed hosts para staging
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "staging.econline.com",
        "staging-api.econline.com",
    ],
)

# Database para staging (similar a producción pero con diferentes credenciales)
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

# CORS settings para staging
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://staging.econline.com",
        "https://staging-frontend.econline.com",
    ],
)

CORS_ORIGIN_WHITELIST = env.list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

# Email backend para staging (puede usar un servicio de pruebas)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# Admin URL para staging
ADMIN_URL = env("ADMIN_URL", default="staging-admin/")

# Simple JWT para staging (tokens un poco más largos que producción para testing)
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
        "REFRESH_TOKEN_LIFETIME": timedelta(hours=12),
        "AUTH_COOKIE_MAX_AGE": 60 * 30,  # 30 minutos
        "AUTH_COOKIE_SAMESITE": "Lax",  # Menos estricto que producción
    }
)

# Braintree para staging (sandbox)
BT_ENVIRONMENT = env("BT_ENVIRONMENT", default="sandbox")

# Rate limiting más relajado para staging
MAX_LOGIN_ATTEMPTS = env.int("MAX_LOGIN_ATTEMPTS", default=10)
LOGIN_ATTEMPT_TIMEOUT = env.int("LOGIN_ATTEMPT_TIMEOUT", default=300)  # 5 minutos

# Logging más verboso para staging
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
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/econline/staging.log",
            "maxBytes": 1024 * 1024 * 25,  # 25 MB
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "payments": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# Sentry para staging con mayor sample rate
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
        traces_sample_rate=0.5,  # Capturar 50% de las transacciones en staging
        send_default_pii=False,
        environment="staging",
        release=env("GIT_COMMIT", default="unknown"),
    )

# Domain settings para staging
DOMAIN = env("DOMAIN", default="https://staging.econline.com")
BACKEND_DOMAIN = env("BACKEND_DOMAIN", default="https://staging-api.econline.com")
SITE_NAME = env("SITE_NAME", default="Econline Staging")

# Configuraciones específicas para testing en staging
if env("ENABLE_DEBUG_TOOLBAR", default=False):
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1", "172.18.0.1"]

# Permitir algunos headers adicionales para testing
CORS_ALLOW_HEADERS += [
    "x-test-user",
    "x-test-scenario",
]
