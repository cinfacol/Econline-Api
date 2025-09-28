#!/bin/bash

echo "🔍 Monitoreando webhooks en tiempo real..."
echo "========================================"
echo ""
echo "✅ Abre otra terminal y haz un pago desde el frontend"
echo "📊 Este script mostrará los logs de webhooks en tiempo real"
echo ""
echo "Presiona Ctrl+C para detener el monitoreo"
echo ""

# Monitorear logs de Django y Celery en tiempo real
docker compose logs -f api celery_worker | grep -E "(webhook|charge|payment_intent|checkout|ERROR|WARN|Task|stripe)" --color=always
