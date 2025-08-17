from django.core.management.base import BaseCommand
from categories.models import MeasureUnit


class Command(BaseCommand):
    help = "Crear unidades de medida por defecto"

    def handle(self, *args, **options):
        # Crear unidades de medida por defecto si no existen
        default_units = [
            "Units",
            "Grams",
            "Pounds",
            "Kilograms",
            "Mililiters",
            "Liters",
            "Other",
        ]

        created_count = 0
        for unit_description in default_units:
            unit, created = MeasureUnit.objects.get_or_create(
                description=unit_description, defaults={"description": unit_description}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Unidad de medida creada: {unit_description}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Unidad de medida ya existe: {unit_description}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso completado. {created_count} unidades de medida creadas."
            )
        )
