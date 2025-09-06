from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Crea perfiles para usuarios que no tengan uno"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-all",
            action="store_true",
            help="Crear perfiles para todos los usuarios sin perfil",
        )

    def handle(self, *args, **options):
        if options["fix_all"]:
            # Encontrar usuarios sin perfil
            users_without_profile = User.objects.filter(profile__isnull=True)

            if not users_without_profile.exists():
                self.stdout.write(
                    self.style.SUCCESS("Todos los usuarios ya tienen perfil")
                )
                return

            created_count = 0
            for user in users_without_profile:
                Profile.objects.create(user=user)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Perfil creado para {user.email}")
                )

            self.stdout.write(
                self.style.SUCCESS(f"Se crearon {created_count} perfiles exitosamente")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Usa --fix-all para crear perfiles para todos los usuarios sin perfil"
                )
            )
