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


# API de Pagos - Documentación

## Autenticación
Todos los endpoints requieren autenticación mediante cookies HTTP-only, excepto el webhook de Stripe. La cookie de sesión se maneja automáticamente por el navegador/Postman.

## Endpoints

### 1. Listar Pagos
```http
GET /api/payments/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

**Query Params (opcionales):**
- status: filtro por estado
- payment_method_id: filtro por método de pago
- search: búsqueda por order_id, email, stripe_payment_intent_id, etc.
- ordering: ordenamiento por created_at, amount, status, payment_method

### 2. Obtener Detalles de un Pago
```http
GET /api/payments/{id}/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

### 3. Calcular Total
```http
GET /api/payments/calculate-total/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

**Query Params:**
- shipping_id: ID del método de envío

### 4. Crear Sesión de Checkout
```http
POST /api/payments/create-checkout-session/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>
- Content-Type: application/json

**Body:**
```json
{
    "shipping_id": "uuid_del_metodo_envio",
    "payment_method_id": "uuid_del_metodo_pago"
}
```

### 5. Procesar Pago
```http
POST /api/payments/{id}/process/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

### 6. Verificar Pago
```http
GET /api/payments/{id}/verify/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

### 7. Reintentar Pago
```http
POST /api/payments/{id}/retry_payment/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

### 8. Obtener Métodos de Pago
```http
GET /api/payments/payment-methods/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

### 9. Reembolsar Pago
```http
POST /api/payments/{id}/refund/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>
- Content-Type: application/json

**Body:**
```json
{
    "reason": "requested_by_customer"
}
```

### 10. Webhook de Stripe
```http
POST /api/payments/webhook/stripe/
```

**Headers:**
- Stripe-Signature: <firma_stripe>
- Content-Type: application/json

**Body:**
<evento_stripe>

### 11. Suscripciones

#### Crear Suscripción
```http
POST /api/payments/subscriptions/create/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>
- Content-Type: application/json

**Body:**
```json
{
    "token": "stripe_token",
    "price_id": "stripe_price_id"
}
```

#### Obtener Suscripción Actual
```http
GET /api/payments/subscriptions/current/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

#### Cancelar Suscripción
```http
POST /api/payments/subscriptions/{id}/cancel/
```

**Headers:**
- Cookie: sessionid=<tu_session_id>

## Configuración en Postman

### 1. Configuración Inicial
- Crear una nueva colección para la API
- Configurar variable de entorno para la URL base (ej: `{{base_url}}`)
- Configurar variable de entorno para la cookie de sesión

### 2. Variables de Entorno
```
base_url: http://tu-dominio.com/api
session_id: <cookie_de_sesion>
```

### 3. Pre-request Script para Autenticación
```javascript
// En la colección de Postman
pm.sendRequest({
    url: pm.variables.get("base_url") + "/auth/login/",
    method: "POST",
    header: {
        "Content-Type": "application/json"
    },
    body: {
        mode: "raw",
        raw: JSON.stringify({
            "email": "tu_email@ejemplo.com",
            "password": "tu_password"
        })
    }
}, function (err, res) {
    if (err) {
        console.error(err);
    } else {
        // La cookie se guardará automáticamente
        console.log("Login exitoso");
    }
});
```

## Flujo de Pago Ejemplo

1. Obtener métodos de pago
```http
GET {{base_url}}/api/payments/payment-methods/
```

2. Calcular total
```http
GET {{base_url}}/api/payments/calculate-total/?shipping_id=<shipping_id>
```

3. Crear sesión de checkout
```http
POST {{base_url}}/api/payments/create-checkout-session/
Body:
{
    "shipping_id": "<shipping_id>",
    "payment_method_id": "<payment_method_id>"
}
```

4. Verificar estado del pago
```http
GET {{base_url}}/api/payments/{id}/verify/
```

5. Procesar pago
```http
POST {{base_url}}/api/payments/{id}/process/
```

## Consideraciones Importantes

1. **Rate Limiting**
   - Los pagos tienen un límite de 3 intentos por minuto

2. **Webhooks**
   - Requieren una firma válida de Stripe
   - Deben ser configurados en el panel de Stripe

3. **Suscripciones**
   - Requieren un token de Stripe válido
   - Solo se permite una suscripción activa por usuario

4. **Manejo de Errores**
   - Todos los endpoints devuelven códigos de estado HTTP apropiados
   - Los errores incluyen mensajes descriptivos en el cuerpo de la respuesta
   - Para errores de autenticación (401), se requiere volver a hacer login

5. **Cookies HTTP-only**
   - Se manejan automáticamente por el navegador/Postman
   - No es necesario configurar manualmente en la mayoría de los casos
