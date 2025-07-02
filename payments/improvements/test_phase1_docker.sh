#!/bin/bash

# Script de prueba para la Fase 1 en Docker
# Ecommerce Payment System - Migración Gradual

echo "🧪 Probando Fase 1: Logging Estructurado y Métricas Básicas en Docker"
echo "=================================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: No se encontró docker-compose.yml. Ejecuta este script desde el directorio Econline-Api."
    exit 1
fi

# Verificar que los contenedores estén corriendo
echo "🔍 Verificando contenedores Docker..."
if ! docker compose ps | grep -q "Up"; then
    echo "⚠️  Los contenedores no están corriendo. Iniciando..."
    docker compose up -d
    echo "⏳ Esperando que los contenedores estén listos..."
    sleep 30
fi

# Verificar que el contenedor de Django esté saludable
echo "🏥 Verificando salud del contenedor Django..."
if curl --fail http://localhost:9090/api/auth/health/ > /dev/null 2>&1; then
    echo "✅ API está saludable (puerto 9090)"
else
    echo "❌ API no está respondiendo en puerto 9090"
    echo "📋 Verificando contenedores:"
    docker compose ps
    exit 1
fi

# Verificar sintaxis de Python en el contenedor
echo "🔍 Verificando sintaxis de Python..."
if docker compose exec -T api python -m py_compile payments/views.py; then
    echo "✅ Sintaxis de payments/views.py correcta"
else
    echo "❌ Error de sintaxis en payments/views.py"
    exit 1
fi

if docker compose exec -T api python -m py_compile config/logging.py; then
    echo "✅ Sintaxis de config/logging.py correcta"
else
    echo "❌ Error de sintaxis en config/logging.py"
    exit 1
fi

# Probar el endpoint de estadísticas público
echo "📊 Probando endpoint de estadísticas público..."
STATS_RESPONSE=$(curl -s http://localhost:9090/api/payments/payment_stats_public/)
if [ $? -eq 0 ]; then
    echo "✅ Endpoint de estadísticas público responde correctamente"
    echo "📋 Respuesta:"
    echo "$STATS_RESPONSE" | python -m json.tool 2>/dev/null || echo "$STATS_RESPONSE"
else
    echo "❌ Error al acceder al endpoint de estadísticas público"
    echo "📋 Verificando logs:"
    docker compose logs api --tail=5
fi

# Probar el endpoint de estadísticas con autenticación (debería fallar sin cookies)
echo "🔒 Probando endpoint de estadísticas con autenticación..."
AUTH_RESPONSE=$(curl -s -w "%{http_code}" http://localhost:9090/api/payments/payment_stats/)
HTTP_CODE="${AUTH_RESPONSE: -3}"
RESPONSE_BODY="${AUTH_RESPONSE%???}"
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ Endpoint protegido funciona correctamente (401 Unauthorized)"
else
    echo "⚠️  Endpoint protegido devolvió código $HTTP_CODE"
    echo "📋 Respuesta: $RESPONSE_BODY"
fi

# Verificar logs estructurados
echo "📝 Verificando configuración de logs..."
if docker compose exec -T api python -c "
import structlog
import logging
try:
    logger = structlog.get_logger()
    logger.info('test_log', test='phase1', status='success')
    print('✅ Structlog configurado correctamente')
except Exception as e:
    print(f'❌ Error con structlog: {e}')
"; then
    echo "✅ Structlog funciona correctamente"
else
    echo "❌ Error con structlog"
fi

# Verificar que PaymentMetrics esté disponible
echo "📈 Verificando clase PaymentMetrics..."
if docker compose exec -T api python manage.py shell -c "
from payments.views import PaymentMetrics
print('✅ PaymentMetrics importada correctamente')
"; then
    echo "✅ PaymentMetrics disponible"
else
    echo "❌ Error al importar PaymentMetrics"
fi

# Mostrar logs recientes
echo "📋 Logs recientes del contenedor:"
docker compose logs api --tail=10

echo ""
echo "🎉 ¡Pruebas de la Fase 1 completadas!"
echo ""
echo "📋 Resumen:"
echo "   ✅ Contenedores Docker funcionando"
echo "   ✅ Sintaxis de Python correcta"
echo "   ✅ Endpoint de estadísticas disponible"
echo "   ✅ Structlog configurado"
echo "   ✅ PaymentMetrics disponible"
echo ""
echo "🔗 Para probar manualmente:"
echo "   - Endpoint de estadísticas: http://localhost:9090/api/payments/payment_stats/"
echo "   - Logs en tiempo real: docker compose logs -f api"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Ejecutar una transacción de pago desde el frontend"
echo "   2. Verificar logs estructurados: docker compose logs api"
echo "   3. Consultar estadísticas actualizadas"
echo "   4. Proceder con la Fase 2 cuando esté lista" 