#!/bin/bash

# Script para probar endpoints con autenticación usando cookies
# Ecommerce Payment System - Fase 1

echo "🔐 Probando endpoints con autenticación (Fase 1)"
echo "================================================"

# Verificar que la API esté funcionando
if ! curl --fail http://localhost:9090/api/auth/health/ > /dev/null 2>&1; then
    echo "❌ API no está respondiendo en puerto 9090"
    exit 1
fi

echo "✅ API está funcionando"

# Crear archivo temporal para cookies
COOKIE_FILE="/tmp/payment_test_cookies.txt"

# Función para limpiar cookies al salir
cleanup() {
    rm -f "$COOKIE_FILE"
}
trap cleanup EXIT

# Intentar login (esto dependerá de tu configuración de autenticación)
echo "🔑 Intentando autenticación..."

# Ejemplo de login (ajustar según tu configuración)
LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -X POST http://localhost:9090/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "password": "testpassword"
    }')

if [ $? -eq 0 ]; then
    echo "📋 Respuesta de login:"
    echo "$LOGIN_RESPONSE" | python -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
    
    # Verificar si hay cookies
    if [ -s "$COOKIE_FILE" ]; then
        echo "✅ Cookies de autenticación obtenidas"
        
        # Probar endpoint protegido con cookies
        echo "🔒 Probando endpoint protegido con autenticación..."
        PROTECTED_RESPONSE=$(curl -s -b "$COOKIE_FILE" http://localhost:9090/api/payments/payment_stats/)
        
        if [ $? -eq 0 ]; then
            echo "✅ Endpoint protegido responde correctamente con autenticación"
            echo "📋 Respuesta:"
            echo "$PROTECTED_RESPONSE" | python -m json.tool 2>/dev/null || echo "$PROTECTED_RESPONSE"
        else
            echo "❌ Error al acceder al endpoint protegido"
        fi
    else
        echo "⚠️  No se obtuvieron cookies de autenticación"
        echo "📋 Verificando si el login fue exitoso..."
        echo "$LOGIN_RESPONSE"
    fi
else
    echo "❌ Error en el proceso de login"
    echo "📋 Respuesta: $LOGIN_RESPONSE"
fi

echo ""
echo "📝 Notas:"
echo "   - Este script asume que tienes un usuario de prueba configurado"
echo "   - Ajusta las credenciales según tu configuración"
echo "   - El endpoint público funciona sin autenticación"
echo "   - El endpoint protegido requiere cookies de sesión" 