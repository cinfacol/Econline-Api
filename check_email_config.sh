#!/bin/bash

echo "📧 Diagnóstico del sistema de correos electrónicos"
echo "================================================="

echo ""
echo "1. 📋 Configuración actual de EMAIL_BACKEND:"
echo "   - En settings.py: console (desarrollo)"
echo "   - En .env: smtp con Mailtrap"

echo ""
echo "2. 🔧 Variables de entorno configuradas:"
docker exec django_api python manage.py shell << 'PYTHON'
from django.conf import settings
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"CELERY_EMAIL_BACKEND: {getattr(settings, 'CELERY_EMAIL_BACKEND', 'No configurado')}")
print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'No configurado')}")
print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'No configurado')}")
print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}")
PYTHON

echo ""
echo "3. 🔍 Verificando logs recientes de emails:"
docker logs celery_worker --tail=20 | grep -i "email\|mail" || echo "   No hay logs de emails recientes"

echo ""
echo "4. 📊 Estado de pagos recientes (últimos 5):"
docker exec django_api python manage.py shell << 'PYTHON'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

recent_payments = Payment.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=2)
).order_by('-created_at')[:5]

for p in recent_payments:
    print(f"Payment {p.id[:8]}... | Status: {p.status} | Email enviado: {p.email_sent} | Usuario: {p.user.email if p.user else 'Sin usuario'}")
PYTHON

echo ""
echo "5. ✅ Recomendaciones:"
echo "   - Para desarrollo: Usa console backend (actual)"
echo "   - Para producción: Cambia a smtp backend"
echo "   - Los emails se muestran en logs de Django cuando usas console backend"
