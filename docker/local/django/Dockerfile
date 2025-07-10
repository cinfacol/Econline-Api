FROM python:3-alpine3.21

ENV APP_HOME=/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

LABEL maintainer='cinfacol@gmail.com'
LABEL youtube="https://www.youtube.com/c/APIImperfect"
LABEL decription="Development image for Real Shop Project"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

RUN pip3 install --upgrade pip

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install -r requirements.txt

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

