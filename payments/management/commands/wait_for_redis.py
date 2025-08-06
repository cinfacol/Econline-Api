from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import redis
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Esperar a que Redis esté disponible"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Tiempo máximo de espera en segundos (default: 30)",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=1.0,
            help="Intervalo entre intentos en segundos (default: 1.0)",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        interval = options["interval"]

        # Configuración para contenedores Docker
        redis_urls = [
            getattr(settings, "REDIS_URL", None),
            getattr(settings, "CELERY_BROKER_URL", None),
            "redis://redis:6379/0",  # Nombre del servicio en Docker Compose
            "redis://localhost:6379/0",  # Fallback local
        ]

        # Filtrar URLs válidas y únicas
        redis_urls = list(filter(None, dict.fromkeys(redis_urls)))

        self.stdout.write("Esperando a que Redis esté disponible...")
        for url in redis_urls:
            self.stdout.write(f"  Probando: {url}")

        start_time = time.time()
        last_error = None

        while time.time() - start_time < timeout:
            for redis_url in redis_urls:
                try:
                    # Intentar conectar a Redis
                    redis_client = redis.Redis.from_url(
                        redis_url,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                    )
                    redis_client.ping()

                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Redis está disponible en {redis_url}")
                    )
                    return redis_url

                except (redis.ConnectionError, redis.TimeoutError) as e:
                    last_error = e
                    logger.debug(f"Fallo al conectar a {redis_url}: {e}")
                    continue

                except Exception as e:
                    last_error = e
                    logger.error(f"Error inesperado al conectar a {redis_url}: {e}")
                    continue

            # Si ninguna URL funcionó, esperar antes del siguiente intento
            self.stdout.write(".", ending="")
            time.sleep(interval)

        # Si llegamos aquí, se agotó el timeout
        self.stdout.write("")  # Nueva línea después de los puntos
        raise CommandError(
            f"Timeout: Redis no está disponible después de {timeout} segundos. "
            f"Último error: {last_error}"
        )
