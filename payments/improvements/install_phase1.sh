#!/bin/bash

# Script de instalación para la Fase 1: Logging Estructurado y Métricas Básicas
# Ecommerce Payment System - Migración Gradual

echo "🚀 Instalando Fase 1: Logging Estructurado y Métricas Básicas"
echo "=========================================================="

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Ejecuta este script desde el directorio raíz del proyecto Django."
    exit 1
fi

# Instalar structlog (opcional)
echo "📦 Instalando structlog..."
pip install structlog

if [ $? -eq 0 ]; then
    echo "✅ structlog instalado correctamente"
else
    echo "⚠️  structlog no se pudo instalar. El sistema funcionará con logging estándar."
fi

# Verificar que los archivos de la Fase 1 existen
echo "🔍 Verificando archivos de la Fase 1..."

if [ -f "payments/views.py" ]; then
    echo "✅ payments/views.py encontrado"
else
    echo "❌ Error: payments/views.py no encontrado"
    exit 1
fi

if [ -f "config/logging_config.py" ]; then
    echo "✅ config/logging_config.py encontrado"
else
    echo "❌ Error: config/logging_config.py no encontrado"
    exit 1
fi

# Configurar logging en manage.py
echo "⚙️  Configurando logging en manage.py..."

# Verificar si ya existe la configuración
if grep -q "setup_payment_logging" manage.py; then
    echo "✅ Logging ya configurado en manage.py"
else
    echo "📝 Agregando configuración de logging a manage.py..."
    # Agregar import al inicio del archivo
    sed -i '1a from config.logging_config import setup_payment_logging' manage.py
    # Agregar llamada después de la configuración de Django
    sed -i '/django.setup()/a setup_payment_logging()' manage.py
    echo "✅ Configuración de logging agregada a manage.py"
fi

# Verificar sintaxis de Python
echo "🔍 Verificando sintaxis de Python..."
python -m py_compile payments/views.py
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis de payments/views.py correcta"
else
    echo "❌ Error de sintaxis en payments/views.py"
    exit 1
fi

python -m py_compile config/logging_config.py
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis de config/logging_config.py correcta"
else
    echo "❌ Error de sintaxis en config/logging_config.py"
    exit 1
fi

# Ejecutar migraciones si es necesario
echo "🔄 Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Verificar que el servidor puede iniciar
echo "🚀 Verificando que el servidor puede iniciar..."
timeout 10s python manage.py runserver --noreload > /dev/null 2>&1
if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo "✅ Servidor puede iniciar correctamente"
else
    echo "❌ Error al iniciar el servidor"
    exit 1
fi

echo ""
echo "🎉 ¡Fase 1 instalada correctamente!"
echo ""
echo "📋 Resumen de cambios:"
echo "   ✅ Logging estructurado integrado"
echo "   ✅ Métricas de pagos implementadas"
echo "   ✅ Endpoint de estadísticas disponible"
echo "   ✅ Método create_checkout_session mejorado"
echo ""
echo "🔗 Endpoints disponibles:"
echo "   - POST /api/payments/{id}/create_checkout_session/ (mejorado)"
echo "   - GET /api/payments/payment_stats/ (nuevo)"
echo ""
echo "📊 Para probar las métricas:"
echo "   curl http://localhost:8000/api/payments/payment_stats/"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Ejecutar una transacción de pago"
echo "   2. Verificar logs en consola"
echo "   3. Consultar estadísticas via endpoint"
echo "   4. Proceder con la Fase 2 cuando esté lista"
echo ""
echo "📚 Documentación: payments/improvements/README_FASE1.md" 