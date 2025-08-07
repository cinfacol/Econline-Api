# Configuración de Webhooks de Stripe - Documentación Final

## 🎯 Estado Actual: ✅ COMPLETAMENTE FUNCIONAL

Los webhooks de Stripe están configurados y funcionando correctamente. Los pagos se actualizan automáticamente de PENDING a COMPLETED.

## 🏗️ Arquitectura Implementada

```
Cliente → Stripe → Webhook → Cloudflare Tunnel → nginx → Django API → Base de Datos
```

## 📋 Configuraciones Implementadas

### 1. URLs de Django (`config/urls.py`)
- ✅ Rutas directas para webhooks sin prefijo `/api/`
- ✅ `stripe_webhook/` para webhooks de producción
- ✅ `webhook_test/` para pruebas

### 2. nginx (`docker/local/nginx/default.conf`)
- ✅ Proxy configurado para enrutar webhooks al contenedor Django
- ✅ Rutas `/stripe_webhook/` y `/webhook_test/`

### 3. Cloudflare Tunnel
- ✅ Ejecutándose en Docker independiente del sistema host
- ✅ Túnel: `econline-api` (ID: 234513a1-cf21-4303-8ff8-9aeeded54300)
- ✅ URL pública: `https://api.virtualeline.com`

### 4. Docker Compose
- ✅ Servicio `cloudflare-tunnel` configurado
- ✅ Credenciales y configuración montadas correctamente

## 🔧 Comandos de Mantenimiento Disponibles

### Diagnóstico de Webhooks
```bash
python manage.py diagnose_webhooks
```

### Diagnóstico de Pagos
```bash
python manage.py diagnose_payments
```

### Procesar Webhooks Pendientes (Backup Manual)
```bash
python manage.py process_pending_webhooks
```

## 📊 Verificación del Estado

### Verificar contenedores
```bash
docker compose ps
```

### Ver logs de webhooks
```bash
docker compose logs api | grep "stripe_webhook"
```

### Ver logs del tunnel
```bash
docker compose logs cloudflare-tunnel
```

### Probar conectividad
```bash
curl https://api.virtualeline.com/webhook_test/ -d '{"test":"ok"}' -H "Content-Type: application/json"
```

## 🚨 Troubleshooting

### Si los webhooks no llegan:
1. Verificar que el tunnel esté funcionando: `docker compose logs cloudflare-tunnel`
2. Verificar configuración en Stripe Dashboard
3. Usar el comando de backup: `python manage.py process_pending_webhooks`

### Si hay errores 502:
1. Verificar que nginx esté funcionando: `docker compose logs nginx`
2. Verificar que Django API esté funcionando: `docker compose logs api`

### Si hay errores de firma:
1. Verificar `STRIPE_WEBHOOK_SECRET` en settings
2. Revisar logs de Django para errores específicos

## 📈 Flujo de Procesamiento

1. **Cliente realiza pago** → Stripe procesa
2. **Stripe envía webhook** → `https://api.virtualeline.com/stripe_webhook/`
3. **Cloudflare Tunnel** → Recibe y reenvía al contenedor
4. **nginx** → Proxy al puerto 8000 del contenedor Django
5. **Django API** → Procesa webhook y actualiza estado del pago
6. **Base de datos** → Estado cambia de PENDING a COMPLETED

## ✅ Verificación de Funcionamiento

- [x] Tunnel de Cloudflare funcionando en Docker
- [x] nginx enrutando webhooks correctamente
- [x] Django procesando webhooks de Stripe
- [x] Pagos actualizándose automáticamente
- [x] Comando de backup disponible para emergencias

---
**Última actualización:** 6 de agosto de 2025
**Estado:** Producción estable ✅
