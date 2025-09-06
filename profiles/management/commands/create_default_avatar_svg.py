import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un avatar SVG de perfil de usuario por defecto"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Sobrescribir archivo existente",
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        avatar_path = os.path.join(media_root, "default_avatar.svg")

        # Crear directorio media si no existe
        os.makedirs(media_root, exist_ok=True)

        # Verificar si ya existe y no se fuerza
        if os.path.exists(avatar_path) and not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    "El archivo default_avatar.svg ya existe. Usa --force para sobrescribir."
                )
            )
            return

        # SVG de perfil de usuario profesional
        svg_content = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Fondo circular con gradiente -->
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4F46E5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7C3AED;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.2"/>
    </filter>
  </defs>

  <!-- Fondo circular -->
  <circle cx="100" cy="100" r="100" fill="url(#bgGradient)" filter="url(#shadow)"/>

  <!-- Silueta de persona -->
  <g fill="white" opacity="0.9">
    <!-- Cabeza -->
    <circle cx="100" cy="70" r="25"/>

    <!-- Cuerpo/hombros -->
    <path d="M 100 95
             C 85 95, 70 100, 60 120
             C 55 130, 55 140, 60 145
             L 140 145
             C 145 140, 145 130, 140 120
             C 130 100, 115 95, 100 95 Z"/>
  </g>

  <!-- Detalles adicionales -->
  <g fill="white" opacity="0.6">
    <!-- Collar/cuello de camisa -->
    <path d="M 85 135 L 100 125 L 115 135 L 115 145 L 85 145 Z"/>
  </g>
</svg>"""

        try:
            # Escribir archivo SVG
            with open(avatar_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Avatar SVG de perfil creado exitosamente en: {avatar_path}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al crear avatar SVG: {str(e)}"))
