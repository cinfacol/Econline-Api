FROM python:3.11.4-slim-buster

ENV APP_HOME=/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

LABEL maintainer='cinfacol@gmail.com'
LABEL youtube="https://www.youtube.com/c/APIImperfect"
LABEL decription="Development image for Real Shop Project"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  && apt-get install -y build-essential \
  && apt-get install -y libpq-dev \
  && apt-get install -y gettext \
  && apt-get install -y curl \
  && apt-get -y install netcat gcc postgresql \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*lear

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

