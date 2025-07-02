"""
Configuración de logging estructurado para el proyecto
Fase 1 de la migración gradual de pagos
"""

import structlog
import logging
from django.conf import settings

def configure_structlog():
    """Configurar structlog para el proyecto"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def setup_payment_logging():
    """Configurar logging específico para pagos"""
    # Configurar structlog si está disponible
    try:
        configure_structlog()
        return True
    except ImportError:
        # Fallback a logging estándar
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return False 