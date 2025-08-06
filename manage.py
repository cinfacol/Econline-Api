#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from config.logging import configure_structlog


def main():
    """Run administrative tasks."""
    # Permitir configurar el entorno con DJANGO_ENVIRONMENT
    environment = os.environ.get("DJANGO_ENVIRONMENT", "development")

    # Mapear entornos a módulos de configuración
    settings_modules = {
        "development": "config.settings.development",
        "staging": "config.settings.staging",
        "production": "config.settings.production",
    }

    # Usar el módulo de configuración apropiado
    default_settings = settings_modules.get(environment, "config.settings.development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_settings)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    configure_structlog()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
