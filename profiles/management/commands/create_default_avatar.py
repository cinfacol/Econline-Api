import os

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw


class Command(BaseCommand):
    help = "Crea una imagen de avatar por defecto si no existe"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Sobrescribir imagen existente",
        )

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        avatar_path = os.path.join(media_root, "default_avatar.png")

        # Crear directorio media si no existe
        os.makedirs(media_root, exist_ok=True)

        # Verificar si ya existe y no se fuerza
        if os.path.exists(avatar_path) and not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    "La imagen default_avatar.png ya existe. Usa --force para sobrescribir."
                )
            )
            return

        try:
            # Crear imagen de 200x200 con gradiente de fondo
            size = (200, 200)

            # Crear imagen con fondo transparente
            image = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            # Crear fondo circular con gradiente simulado
            center = (100, 100)
            radius = 100

            # Dibujar círculo de fondo con gradiente simulado (múltiples círculos)
            for i in range(radius, 0, -2):
                # Interpolación de color para simular gradiente
                factor = i / radius
                r = int(79 + (124 - 79) * (1 - factor))  # De #4F46E5 a #7C3AED
                g = int(70 + (58 - 70) * (1 - factor))
                b = int(229 + (237 - 229) * (1 - factor))
                color = (r, g, b, 255)

                draw.ellipse(
                    [center[0] - i, center[1] - i, center[0] + i, center[1] + i],
                    fill=color,
                )

            # Dibujar silueta de persona en blanco
            person_color = (255, 255, 255, 230)  # Blanco semi-transparente

            # Cabeza (círculo)
            head_center = (100, 70)
            head_radius = 25
            draw.ellipse(
                [
                    head_center[0] - head_radius,
                    head_center[1] - head_radius,
                    head_center[0] + head_radius,
                    head_center[1] + head_radius,
                ],
                fill=person_color,
            )

            # Cuerpo/hombros (usando polígono para simular la forma)
            body_points = [
                (100, 95),  # Punto superior centro
                (75, 100),  # Hombro izquierdo
                (60, 120),  # Lado izquierdo
                (55, 140),  # Parte baja izquierda
                (145, 140),  # Parte baja derecha
                (140, 120),  # Lado derecho
                (125, 100),  # Hombro derecho
            ]
            draw.polygon(body_points, fill=person_color)

            # Collar/cuello (detalle adicional)
            collar_color = (255, 255, 255, 150)
            collar_points = [(85, 135), (100, 125), (115, 135), (115, 145), (85, 145)]
            draw.polygon(collar_points, fill=collar_color)

            # Convertir a RGB para guardar como PNG
            if image.mode == "RGBA":
                # Crear fondo blanco y combinar
                rgb_image = Image.new("RGB", size, (255, 255, 255))
                rgb_image.paste(
                    image, mask=image.split()[-1]
                )  # Usar canal alpha como máscara
                image = rgb_image

            # Guardar imagen
            image.save(avatar_path, "PNG")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Avatar de perfil de usuario creado exitosamente en: {avatar_path}"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error al crear avatar por defecto: {str(e)}")
            )
