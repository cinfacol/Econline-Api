FROM python:alpine3.22

ENV APP_HOME=/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

LABEL maintainer='cinfacol@gmail.com'
LABEL youtube="https://www.youtube.com/c/APIImperfect"
LABEL description="Development image for Real Shop Project - Optimized with uv"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apk update && apk add --no-cache \
    build-base \
    postgresql-dev \
    gettext \
    curl \
    netcat-openbsd \
    libffi-dev \
    openssl-dev \
    jpeg-dev \
    zlib-dev \
    bash

# Instalar uv - herramienta ultra-rápida para gestión de paquetes Python
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Configurar uv para máximo rendimiento
ENV UV_SYSTEM_PYTHON=1
ENV UV_CACHE_DIR=/root/.cache/uv
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON=/usr/local/bin/python3

# Crear directorio de caché y configurar permisos
RUN mkdir -p /root/.cache/uv && chmod -R 755 /root/.cache

# Copiar archivos de proyecto PRIMERO (para aprovechar el caché de Docker)
COPY ./pyproject.toml ./uv.lock /app/

# Sincronizar dependencias usando el lock file (enfoque moderno)
# Usamos --no-dev para solo instalar dependencias de producción
RUN cd /app && uv sync --no-dev --python /usr/local/bin/python3

# Corregir el enlace simbólico de Python en el virtual environment
RUN rm -f /app/.venv/bin/python /app/.venv/bin/python3 /app/.venv/bin/python3.12
RUN ln -s /usr/local/bin/python3 /app/.venv/bin/python
RUN ln -s /usr/local/bin/python3 /app/.venv/bin/python3
RUN ln -s /usr/local/bin/python3 /app/.venv/bin/python3.12

# Configurar el entorno virtual creado por uv en el PATH
ENV PATH="/app/.venv/bin:$PATH"

# Verificar que las dependencias se instalaron correctamente
RUN cd /app && python -c "import django; import psycopg2; print('Dependencies OK')"

COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./docker/local/django/celery/worker/start /start-celery_worker
RUN sed -i 's/\r$//g' /start-celery_worker
RUN chmod +x /start-celery_worker

COPY ./docker/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

# Crear un usuario no privilegiado
# RUN addgroup --system celeryuser && adduser --system --ingroup celeryuser celeryuser

# Cambiar al usuario no privilegiado
# USER celeryuser

ENTRYPOINT [ "/entrypoint.sh"]

