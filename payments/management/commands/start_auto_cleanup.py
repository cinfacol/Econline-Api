import logging

from django.core.management.base import BaseCommand

from payments.tasks import clean_expired_sessions_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Iniciar la limpieza automática de sesiones expiradas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delay",
            type=int,
            default=300,
            help="Retraso inicial en segundos antes de la primera ejecución (default: 300)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecutar sin hacer cambios reales",
        )

    def handle(self, *args, **options):
        delay = options["delay"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Ejecutando en modo DRY RUN - No se iniciará la limpieza automática"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Iniciando limpieza automática de sesiones expiradas (delay inicial: {delay}s)"
            )
        )

        try:
            # Programar la primera ejecución
            task_result = clean_expired_sessions_task.apply_async(countdown=delay)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Limpieza automática programada\n"
                    f"   - Task ID: {task_result.id}\n"
                    f"   - Primera ejecución en: {delay} segundos\n"
                    f"   - La tarea se reprogramará automáticamente"
                )
            )

            self.stdout.write(
                self.style.WARNING(
                    "💡 Para monitorear el progreso:\n"
                    "   - Revisar logs: docker-compose logs -f celery_worker\n"
                    "   - Flower UI: http://localhost:5557\n"
                    "   - Comando manual: python manage.py clean_expired_sessions"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error iniciando limpieza automática: {str(e)}")
            )
            logger.error(f"Error iniciando limpieza automática: {str(e)}")
            raise
