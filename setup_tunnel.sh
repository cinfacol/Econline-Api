#!/bin/bash
# Script para configurar Cloudflare Tunnel completamente independiente
# Ejecutar este script una sola vez para configurar el tunnel

set -e

echo "🔧 Configurando Cloudflare Tunnel independiente para Econline API"
echo "================================================================"

# Verificar que cloudflared esté instalado
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared no está instalado. Instalando..."
    
    # Detectar arquitectura
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        ARCH="arm64"
    fi
    
    # Descargar e instalar cloudflared
    wget -O cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    echo "✅ cloudflared instalado"
fi

# Crear directorio de configuración si no existe
mkdir -p ./cloudflare

echo ""
echo "🔑 PASO 1: Autenticación"
echo "------------------------"
echo "Se abrirá tu navegador para autenticar con Cloudflare."
echo "Si ya tienes un token, puedes saltarte este paso."
read -p "¿Continuar con la autenticación? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cloudflared tunnel login
fi

echo ""
echo "🚇 PASO 2: Crear tunnel"
echo "----------------------"
read -p "¿Crear nuevo tunnel 'econline-api'? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Crear el tunnel
    cloudflared tunnel create econline-api
    
    # Copiar las credenciales al proyecto
    TUNNEL_ID=$(cloudflared tunnel list | grep econline-api | awk '{print $1}')
    cp ~/.cloudflared/${TUNNEL_ID}.json ./cloudflare/credentials.json
    
    echo "✅ Tunnel creado y credenciales copiadas"
    echo "📋 Tunnel ID: $TUNNEL_ID"
    
    # Actualizar el archivo de configuración con el ID real
    sed -i "s/tunnel: econline-api/tunnel: $TUNNEL_ID/" ./cloudflare/config.yml
fi

echo ""
echo "🌐 PASO 3: Configurar DNS"
echo "------------------------"
echo "Necesitas configurar los siguientes registros DNS en Cloudflare:"
echo ""
echo "Tipo: CNAME"
echo "Nombre: api"
echo "Destino: [TUNNEL_ID].cfargotunnel.com"
echo ""
read -p "¿Configurar DNS automáticamente? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cloudflared tunnel route dns econline-api api.virtualeline.com
    echo "✅ DNS configurado para api.virtualeline.com"
fi

echo ""
echo "🚀 PASO 4: Iniciar tunnel en Docker"
echo "----------------------------------"
read -p "¿Iniciar el servicio de tunnel en Docker? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose up cloudflare-tunnel -d
    echo "✅ Tunnel iniciado en Docker"
fi

echo ""
echo "🎉 CONFIGURACIÓN COMPLETADA"
echo "=========================="
echo ""
echo "✅ Tunnel configurado independientemente en el proyecto"
echo "✅ Credenciales guardadas en ./cloudflare/credentials.json"
echo "✅ Configuración en ./cloudflare/config.yml"
echo ""
echo "🔗 Tu API debería estar disponible en:"
echo "   https://api.virtualeline.com"
echo ""
echo "🧪 Para probar:"
echo "   curl https://api.virtualeline.com/api/payments/webhook-test/"
echo ""
echo "📋 Para monitorear el tunnel:"
echo "   docker logs cloudflare_tunnel -f"
