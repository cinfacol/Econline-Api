# Virtualeline-Api
Backend de ecommerce con django restframework
Frontend: ~/Escritorio/Programacion/Tienda/client

celery, activación

1. estando los servicios de redis detenidos escribimos en un bash dentro del entorno virtual
    $ redis-server  //Ready to accept connections
2. en otro terminal 
    $ python -m celery -A config worker // config es donde se encuentra el archivo settings de django
3. en otro terminal y también en el ambiente virtual corremos el servidor django
    $ python manage.py runserver

### Páginas de interes para pagos con stripe
1. https://docs.stripe.com/api/payment_intents/object
2. https://codingpr.com/
3. https://github.com/jameshenry2020/-Stripe-Payment-processing-in-Django-rest-framework-Backend/blob/main/payment/views.py
4. https://www.youtube.com/watch?v=rKD5bhoTeFw
5. https://episyche.com/blog/how-to-integrate-stripe-payment-gateway-in-django-and-react-for-the-checkout-use-case
6. https://dev.to/documatic/integrate-stripe-payments-with-django-by-building-a-digital-products-selling-app-le5
7. https://github.com/dotpep/fullstack-ecommerce/tree/main
8. https://github.com/earthcomfy/django-ecommerce-api/tree/master

cambio para probar rule master-protect
