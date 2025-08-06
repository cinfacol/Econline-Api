"""
Archivo principal de configuración que determina qué configuración usar
basado en la variable de entorno DJANGO_SETTINGS_MODULE
"""

import os

# Determinar el entorno actual
environment = os.environ.get("DJANGO_ENVIRONMENT", "development")

if environment == "production":
    from .production import *
elif environment == "staging":
    from .staging import *
else:
    from .development import *

# Permitir override manual con DJANGO_SETTINGS_MODULE
# Esto mantiene compatibilidad con el comportamiento estándar de Django
