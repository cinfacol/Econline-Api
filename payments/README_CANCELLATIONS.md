# Gestión de Cancelaciones y Sesiones Expiradas

Este documento describe las mejoras implementadas para manejar cancelaciones de pagos y sesiones expiradas de Stripe en un entorno de contenedores con HTTP-only cookies.

## Problema Original

Cuando se cancelaba una orden desde el frontend, no se enviaba el evento `payment_intent.payment_failed` a Stripe, por lo que el webhook no se disparaba y el pedido permanecía en estado pendiente.

## Solución Implementada

### 1. Nuevas Tareas (Tasks)

#### `handle_manual_payment_cancellation_task`
- Maneja cancelaciones manuales de pagos
- Actualiza el estado del pago a `CANCELLED`
- Actualiza el estado de la orden a `CANCELLED`
- Libera el inventario reservado
- Limpia los cupones del carrito
- **Mejorado para contenedores**: Manejo robusto de errores y reintentos

#### `handle_checkout_session_expired_task` (Mejorada)
- Maneja la expiración de sesiones de checkout
- Verifica que el pago no esté ya completado antes de cancelar
- Libera inventario y limpia cupones
- **Mejorado para contenedores**: Imports dinámicos para evitar problemas circulares

#### `clean_expired_sessions_task`
- Tarea inteligente que se auto-reprograma
- Verifica automáticamente sesiones expiradas
- Se ejecuta cada 5-15 minutos dependiendo de la actividad
- **Ventaja**: No requiere Celery Beat, funciona solo con Celery Worker

### 2. Nuevos Endpoints

#### `POST /api/payments/{id}/cancel/`
Cancela un pago específico de forma síncrona:
```json
{
    "status": "cancelled",
    "payment_id": "uuid",
    "order_id": "uuid",
    "message": "Pago cancelado exitosamente",
    "payment_status": "CANCELLED",
    "order_status": "CANCELLED"
}
```

#### `POST /api/payments/check_expired_sessions/`
Inicia limpieza de sesiones expiradas (solo staff):
```json
{
    "message": "Limpieza de sesiones expiradas iniciada",
    "task_id": "task-uuid",
    "status": "started",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### `GET /api/payments/{id}/status/`
Obtiene el estado actual del pago:
```json
{
    "payment_id": "uuid",
    "order_id": "uuid",
    "payment_status": "CANCELLED",
    "payment_status_display": "Cancelado",
    "order_status": "CANCELLED",
    "order_status_display": "Cancelado",
    "amount": "100.00",
    "currency": "USD",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z",
    "stripe": {
        "session_id": "cs_xxx",
        "session_status": "expired",
        "payment_status": "unpaid",
        "expires_at": 1704115200,
        "checkout_url": null
    }
}
```

#### `POST /api/payments/{id}/sync_status/`
Sincroniza el estado del pago con Stripe:
```json
{
    "status": "expired",
    "message": "La sesión ha expirado y se está procesando la cancelación",
    "payment_status": "P",
    "stripe_status": "expired",
    "task_id": "task-uuid"
}
```

#### `GET /api/payments/task_status/?task_id={task_id}`
Verifica el estado de una tarea de Celery:
```json
{
    "task_id": "task-uuid",
    "status": "SUCCESS",
    "ready": true,
    "result": {
        "status": "success",
        "payment_id": "uuid",
        "order_id": "uuid"
    },
    "message": "Tarea completada exitosamente"
}
```

#### `GET /api/payments/test_cancellation/`
Endpoint de prueba para verificar pagos (solo desarrollo/staff):

#### `POST /api/payments/{id}/debug_cancel/`
Endpoint de debug para cancelar un pago y verificar el proceso (solo desarrollo/staff):
```json
{
    "message": "Cancelación completada",
    "debug_info": {
        "request_user": "user@example.com",
        "payment_user": "user@example.com",
        "payment_id": "uuid",
        "order_id": "uuid",
        "initial_payment_status": "PENDING",
        "initial_order_status": "PENDING",
        "final_payment_status": "CANCELLED",
        "final_order_status": "CANCELLED",
        "cancel_successful": true,
        "user_authorized": true,
        "can_cancel": true
    },
    "response": {
        "status": "cancelled",
        "payment_id": "uuid",
        "order_id": "uuid",
        "message": "Pago cancelado exitosamente"
    }
}
```
```json
{
    "message": "Encontrados 2 pagos para probar",
    "payments": [
        {
            "payment_id": "uuid",
            "order_id": "uuid",
            "payment_status": "PENDING",
            "payment_status_display": "Pendiente",
            "order_status": "PENDING",
            "order_status_display": "Pendiente",
            "amount": "100.00",
            "currency": "USD",
            "user_email": "user@example.com",
            "stripe_session_id": "cs_xxx",
            "created_at": "2024-01-01T12:00:00Z",
            "stripe": {
                "session_status": "open",
                "payment_status": "unpaid",
                "expires_at": 1704115200
            }
        }
    ],
    "test_endpoints": {
        "cancel": "POST /api/payments/{payment_id}/cancel/",
        "status": "GET /api/payments/{payment_id}/status/",
        "sync": "POST /api/payments/{payment_id}/sync_status/"
    }
}
```

### 3. Comandos de Gestión

#### `python manage.py clean_expired_sessions`
Limpia sesiones expiradas desde la línea de comandos:

```bash
# Ejecutar sin hacer cambios (dry run)
python manage.py clean_expired_sessions --dry-run

# Ejecutar con limpieza forzada
python manage.py clean_expired_sessions --force

# Ejecutar normalmente
python manage.py clean_expired_sessions
```

#### `python manage.py start_auto_cleanup`
Inicia la limpieza automática:

```bash
# Iniciar con delay personalizado (5 minutos)
python manage.py start_auto_cleanup --delay 300

# Modo dry run
python manage.py start_auto_cleanup --dry-run
```

#### `python manage.py test_cancellation`
Prueba la cancelación de pagos:

```bash
# Probar con un pago específico
python manage.py test_cancellation --payment-id uuid

# Probar pagos de un usuario específico
python manage.py test_cancellation --user-email user@example.com

# Modo dry run (sin hacer cambios)
python manage.py test_cancellation --dry-run

# Probar integración con Stripe
python manage.py test_cancellation --stripe-test

# Combinar opciones
python manage.py test_cancellation --user-email user@example.com --dry-run --stripe-test
```

#### `python manage.py check_payment_status`
Monitorea el estado de los pagos en tiempo real:

```bash
# Monitorear un pago específico
python manage.py check_payment_status --payment-id uuid

# Monitorear pagos de un usuario
python manage.py check_payment_status --user-email user@example.com

# Monitorear continuamente (hasta Ctrl+C)
python manage.py check_payment_status --watch

# Monitorear por 2 minutos con intervalos de 10 segundos
python manage.py check_payment_status --duration 120 --interval 10

# Monitorear pagos pendientes por defecto
python manage.py check_payment_status --watch
```

#### `python manage.py wait_for_redis`
Espera a que Redis esté disponible (útil para contenedores):

```bash
# Esperar con timeout personalizado
python manage.py wait_for_redis --timeout 60 --interval 2
```

### 4. Configuración Automática

La tarea `clean_expired_sessions_task` se auto-reprograma:
- **Si encuentra problemas**: Se ejecuta cada 5 minutos
- **Si todo está bien**: Se ejecuta cada 15 minutos
- **Si hay errores**: Se reintenta cada 10 minutos

## ¿Por qué NO usar Celery Beat?

### **Ventajas de usar solo Celery Worker:**

1. **Simplicidad**: Menos servicios que mantener
2. **Flexibilidad**: La tarea se adapta automáticamente a la carga
3. **Eficiencia**: Solo se ejecuta cuando es necesario
4. **Robustez**: Menos puntos de fallo
5. **Recursos**: Menor consumo de memoria y CPU

### **Cuándo usar Celery Beat:**

- Tareas que deben ejecutarse en horarios específicos
- Tareas que no dependen del estado del sistema
- Cuando necesitas control granular sobre el timing

### **Cuándo usar auto-reprogramación:**

- Tareas que dependen del estado del sistema
- Tareas que deben adaptarse a la carga
- Cuando quieres simplicidad en la infraestructura

## Configuración para Contenedores

### Variables de Entorno Requeridas

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True

# Redis
REDIS_URL=redis://redis:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Docker Compose

El archivo `docker-compose.yml` incluye solo:

```yaml
celery_worker:
    # Worker para procesar tareas (incluye limpieza automática)
    command: /start-celery_worker
```

### Scripts de Inicio

- `/start-celery_worker`: Inicia el worker de Celery con limpieza automática

## Flujo de Cancelación

### Cancelación Manual (Frontend)
1. Usuario cancela desde el frontend
2. Se llama a `POST /api/payments/{id}/cancel/`
3. Se cancela el PaymentIntent en Stripe (si existe)
4. Se actualiza el estado del pago y orden a `CANCELLED` de forma síncrona
5. Se libera el inventario y se limpian los cupones
6. Se devuelve confirmación inmediata al frontend

### Expiración de Sesión
1. Stripe envía webhook `checkout.session.expired`
2. Se ejecuta `handle_checkout_session_expired_task`
3. Se actualiza el estado del pago y orden a `CANCELLED`
4. Se libera el inventario y se limpian los cupones

### Limpieza Automática
1. `clean_expired_sessions_task` se ejecuta automáticamente
2. Se verifican todos los pagos pendientes con sesiones de Stripe
3. Se procesan las sesiones expiradas automáticamente
4. La tarea se reprograma según los resultados

## Estados de Pago

- `PENDING`: Pago pendiente
- `COMPLETED`: Pago completado
- `FAILED`: Pago fallido
- `CANCELLED`: Pago cancelado
- `REFUNDED`: Pago reembolsado

## Estados de Orden

## Troubleshooting

### Problema: El pago sigue apareciendo como pendiente después de cancelar

**Síntomas:**
- El frontend muestra que el pago fue cancelado
- Pero en la base de datos sigue apareciendo como `PENDING`

**Causas posibles:**
1. La cancelación se procesó de forma asíncrona y falló
2. Error en la comunicación con Stripe
3. Problema de concurrencia en la base de datos

**Soluciones:**

#### 1. Verificar el estado actual
```bash
# Usar el comando de prueba
python manage.py test_cancellation --payment-id <payment_id>

# O usar el endpoint de prueba
GET /api/payments/test_cancellation/?payment_id=<payment_id>
```

#### 2. Verificar manualmente en la base de datos
```sql
-- Verificar estado del pago
SELECT id, status, error_message, updated_at 
FROM payments_payment 
WHERE id = '<payment_id>';

-- Verificar estado de la orden
SELECT id, status, updated_at 
FROM orders_order 
WHERE id = '<order_id>';
```

#### 3. Forzar cancelación manual
```bash
# Usar el comando con modo real (no dry-run)
python manage.py test_cancellation --payment-id <payment_id>
```

#### 4. Verificar logs de Celery
```bash
# Ver logs del worker de Celery
docker-compose logs celery_worker

# Buscar errores específicos
docker-compose logs celery_worker | grep -i "payment\|cancel"
```

#### 5. Verificar integración con Stripe
```bash
# Probar con integración de Stripe
python manage.py test_cancellation --payment-id <payment_id> --stripe-test
```

### Problema: Error "Payment not found" al cancelar

**Causa:** El pago no existe o el usuario no tiene permisos

**Solución:**
```bash
# Verificar que el pago existe
python manage.py test_cancellation --payment-id <payment_id> --dry-run

# Verificar pagos del usuario
python manage.py test_cancellation --user-email <email> --dry-run
```

### Problema: Error de Stripe al cancelar

**Síntomas:**
- Error en logs: "Error al cancelar PaymentIntent en Stripe"
- El pago se cancela localmente pero hay warning

**Solución:**
1. Verificar que las credenciales de Stripe sean correctas
2. Verificar que el PaymentIntent existe en Stripe
3. El pago se cancela localmente de todas formas, el error de Stripe no es crítico

### Problema: Celery Worker no está procesando tareas

**Síntomas:**
- Las tareas quedan en estado "PENDING"
- No hay logs de Celery

**Solución:**
```bash
# Verificar que el worker esté corriendo
docker-compose ps celery_worker

# Reiniciar el worker
docker-compose restart celery_worker

# Verificar logs
docker-compose logs celery_worker
```

### Problema: Redis no está disponible

**Síntomas:**
- Error de conexión a Redis
- Celery no puede procesar tareas

**Solución:**
```bash
# Esperar a que Redis esté disponible
python manage.py wait_for_redis

# Verificar estado de Redis
docker-compose ps redis

# Reiniciar Redis si es necesario
docker-compose restart redis
```

## Comandos Útiles para Debugging

### Verificar estado de pagos
```bash
# Ver todos los pagos pendientes
python manage.py shell -c "
from payments.models import Payment
payments = Payment.objects.filter(status='P').select_related('order', 'user')
for p in payments:
    print(f'ID: {p.id}, User: {p.user.email}, Amount: {p.amount}, Created: {p.created_at}')
"
```

### Verificar sesiones de Stripe
```bash
# Ver sesiones expiradas
python manage.py shell -c "
import stripe
from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY
sessions = stripe.checkout.Session.list(limit=10)
for s in sessions.data:
    print(f'ID: {s.id}, Status: {s.status}, Payment: {s.payment_status}, Expires: {s.expires_at}')
"
```

### Verificar inventario
```bash
# Ver inventario liberado
python manage.py shell -c "
from inventory.models import InventoryStock
stocks = InventoryStock.objects.all()
for s in stocks:
    print(f'Product: {s.inventory.product.name}, Units: {s.units}, Sold: {s.units_sold}')
"
```

- `PENDING`: Orden pendiente
- `COMPLETED`: Orden completada
- `CANCELLED`: Orden cancelada
- `SHIPPED`: Orden enviada
- `DELIVERED`: Orden entregada

## Monitoreo

### Logs
Todos los eventos se registran con el logger `payments`:
- Cancelaciones manuales
- Expiración de sesiones
- Errores de sincronización
- Limpieza automática

### Métricas
Se pueden consultar las estadísticas de pagos en:
- `GET /api/payments/payment_stats/`
- `GET /api/payments/payment_stats_public/`

### Flower (Monitoreo de Celery)
Accesible en `http://localhost:5557` para monitorear tareas de Celery.

## Consideraciones para HTTP-Only Cookies

### Autenticación
- Los endpoints verifican la autenticación usando las cookies HTTP-only
- Se incluyen verificaciones de permisos para contenedores
- Los endpoints de administración requieren permisos de staff

### Seguridad
- Las cookies HTTP-only previenen acceso desde JavaScript
- Se implementan verificaciones de autorización en cada endpoint
- Los tokens de tareas se devuelven para seguimiento

## Recomendaciones

1. **Monitoreo**: Revisar logs regularmente para detectar problemas
2. **Limpieza Manual**: Ejecutar `clean_expired_sessions` periódicamente en producción
3. **Webhooks**: Asegurar que Stripe esté configurado para enviar `checkout.session.expired`
4. **Celery**: Verificar que Celery Worker esté ejecutándose
5. **Contenedores**: Usar health checks para verificar el estado de los servicios
6. **Redis**: Monitorear la conexión a Redis en contenedores
7. **Auto-limpieza**: Iniciar con `start_auto_cleanup` después del deploy

## Troubleshooting

### Sesiones que no se cancelan
1. Verificar que el webhook `checkout.session.expired` esté configurado en Stripe
2. Ejecutar `clean_expired_sessions --dry-run` para diagnosticar
3. Revisar logs de Celery para errores en tareas
4. Verificar que Redis esté disponible en contenedores

### Estados inconsistentes
1. Usar `sync_status` para sincronizar manualmente
2. Verificar que las tareas se estén ejecutando correctamente
3. Comprobar la conectividad entre contenedores

### Inventario no liberado
1. Verificar que el método `release_inventory` esté funcionando
2. Revisar logs para errores en la liberación de inventario
3. Ejecutar limpieza manual si es necesario
4. Verificar la conectividad a la base de datos

### Problemas de Contenedores
1. Verificar que todos los servicios estén ejecutándose: `docker-compose ps`
2. Revisar logs de contenedores: `docker-compose logs celery_worker`
3. Verificar conectividad entre servicios
4. Comprobar variables de entorno en contenedores

### Problemas de Redis
1. Verificar que Redis esté ejecutándose: `docker-compose logs redis`
2. Comprobar conectividad: `python manage.py wait_for_redis`
3. Verificar configuración de Celery
4. Revisar logs de Celery para errores de conexión

### Limpieza automática no funciona
1. Verificar que se haya iniciado: `python manage.py start_auto_cleanup`
2. Revisar logs de Celery: `docker-compose logs -f celery_worker`
3. Verificar que la tarea esté en la cola: Flower UI
4. Comprobar que Redis esté funcionando correctamente 