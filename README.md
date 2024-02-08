# Econline-Api
Backend de ecommerce con django restframework
Frontend: ~/Escritorio/Programacion/Tienda/client

celery, activación

1. estando los servicios de redis detenidos escribimos en un bash dentro del entorno virtual
    $ redis-server  //Ready to accept connections
2. en otro terminal 
    $ python -m celery -A config worker // config es donde se encuentra el archivo settings de django
3. en otro terminal y también en el ambiente virtual corremos el servidor django
    $ python manage.py runserver
