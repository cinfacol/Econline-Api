#!/bin/bash

set -o errexit

set -o pipefail

set -o nounset

postgres_ready() {
python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${POSTGRES_DB}",
        user="${POSTGRES_USER}",
        password="${POSTGRES_PASSWORD}",
        host="${PG_HOST}",
        port="${PG_PORT}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
 >&2 echo "Waiting for PostgreSQL to become available....:-("
 sleep 1
done
>&2 echo "PostgreSQL is ready!!!!...:-)"

# Crear directorio de media files si no existe
mkdir -p /app/mediafiles

# Crear avatar por defecto si no existe
if [ ! -f "/app/mediafiles/default_avatar.png" ]; then
    >&2 echo "Creating default user profile avatar (PNG)..."
    python -c "
import os
from PIL import Image, ImageDraw

# Crear imagen de 200x200
size = (200, 200)

# Crear imagen con fondo transparente
image = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Crear fondo circular con gradiente simulado
center = (100, 100)
radius = 100

# Dibujar círculo de fondo con gradiente simulado
for i in range(radius, 0, -2):
    factor = i / radius
    r = int(79 + (124 - 79) * (1 - factor))  # De #4F46E5 a #7C3AED
    g = int(70 + (58 - 70) * (1 - factor))
    b = int(229 + (237 - 229) * (1 - factor))
    color = (r, g, b, 255)
    
    draw.ellipse([center[0] - i, center[1] - i, 
                  center[0] + i, center[1] + i], fill=color)

# Dibujar silueta de persona en blanco
person_color = (255, 255, 255, 230)

# Cabeza
head_center = (100, 70)
head_radius = 25
draw.ellipse([head_center[0] - head_radius, head_center[1] - head_radius,
              head_center[0] + head_radius, head_center[1] + head_radius], 
             fill=person_color)

# Cuerpo/hombros
body_points = [
    (100, 95), (75, 100), (60, 120), (55, 140),
    (145, 140), (140, 120), (125, 100)
]
draw.polygon(body_points, fill=person_color)

# Collar/cuello
collar_points = [(85, 135), (100, 125), (115, 135), (115, 145), (85, 145)]
draw.polygon(collar_points, fill=(255, 255, 255, 150))

# Convertir a RGB y guardar PNG
if image.mode == 'RGBA':
    rgb_image = Image.new('RGB', size, (255, 255, 255))
    rgb_image.paste(image, mask=image.split()[-1])
    image = rgb_image

image.save('/app/mediafiles/default_avatar.png', 'PNG')
print('Professional user profile avatar (PNG) created successfully!')
" || >&2 echo "Warning: Could not create default avatar PNG"
fi

# Crear avatar SVG por defecto si no existe
if [ ! -f "/app/mediafiles/default_avatar.svg" ]; then
    >&2 echo "Creating default user profile avatar (SVG)..."
    cat > /app/mediafiles/default_avatar.svg << 'EOF'
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
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
</svg>
EOF
    >&2 echo "Professional user profile avatar (SVG) created successfully!"
fi

exec "$@"
