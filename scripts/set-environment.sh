#!/bin/bash

# Script para cambiar entre entornos de configuración
# Uso: ./scripts/set-environment.sh [development|staging|production]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Uso: $0 [environment]${NC}"
    echo ""
    echo "Entornos disponibles:"
    echo -e "  ${GREEN}development${NC} - Entorno de desarrollo local"
    echo -e "  ${YELLOW}staging${NC}     - Entorno de staging/testing"
    echo -e "  ${RED}production${NC}  - Entorno de producción"
    echo ""
    echo "Ejemplos:"
    echo "  $0 development"
    echo "  $0 staging"
    echo "  $0 production"
    echo ""
    echo "El script:"
    echo "  1. Configura la variable DJANGO_ENVIRONMENT"
    echo "  2. Copia el archivo .env apropiado (si existe)"
    echo "  3. Muestra instrucciones adicionales"
}

# Validar argumentos
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

ENVIRONMENT=$1

# Validar entorno
case $ENVIRONMENT in
    development|dev)
        ENVIRONMENT="development"
        ENV_FILE=".env"
        ENV_EXAMPLE=".env.example"
        COLOR=$GREEN
        ;;
    staging|stage)
        ENVIRONMENT="staging"
        ENV_FILE=".env.staging"
        ENV_EXAMPLE=".env.staging.example"
        COLOR=$YELLOW
        ;;
    production|prod)
        ENVIRONMENT="production"
        ENV_FILE=".env.production"
        ENV_EXAMPLE=".env.production.example"
        COLOR=$RED
        ;;
    *)
        echo -e "${RED}❌ Error: Entorno '$1' no válido${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo -e "${COLOR}🔧 Configurando entorno: $ENVIRONMENT${NC}"
echo ""

# Cambiar al directorio del proyecto
cd "$PROJECT_ROOT"

# Crear archivo de configuración de entorno
echo "DJANGO_ENVIRONMENT=$ENVIRONMENT" > .django-env

# Configurar archivo .env si existe el example
if [ -f "$ENV_EXAMPLE" ]; then
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}📝 Copiando $ENV_EXAMPLE a $ENV_FILE${NC}"
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${YELLOW}⚠️  IMPORTANTE: Edita el archivo $ENV_FILE con tus configuraciones reales${NC}"
    else
        echo -e "${GREEN}✅ El archivo $ENV_FILE ya existe${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Archivo $ENV_EXAMPLE no encontrado${NC}"
fi

# Mostrar configuración actual
echo ""
echo -e "${COLOR}📋 Configuración actual:${NC}"
echo "  Entorno: $ENVIRONMENT"
echo "  Archivo de settings: config.settings.$ENVIRONMENT"
echo "  Variables de entorno: $ENV_FILE"

# Mostrar comandos útiles
echo ""
echo -e "${BLUE}🚀 Comandos útiles para este entorno:${NC}"

case $ENVIRONMENT in
    development)
        echo "  # Ejecutar servidor de desarrollo"
        echo "  python manage.py runserver"
        echo ""
        echo "  # O con Docker"
        echo "  docker-compose up --build"
        ;;
    staging)
        echo "  # Construir para staging"
        echo "  docker-compose -f docker-compose.staging.yml up --build"
        echo ""
        echo "  # Ejecutar migraciones"
        echo "  DJANGO_ENVIRONMENT=staging python manage.py migrate"
        ;;
    production)
        echo "  # Construir para producción"
        echo "  docker-compose -f docker-compose.prod.yml up --build -d"
        echo ""
        echo "  # Ejecutar migraciones"
        echo "  DJANGO_ENVIRONMENT=production python manage.py migrate"
        echo ""
        echo "  # Recolectar archivos estáticos"
        echo "  DJANGO_ENVIRONMENT=production python manage.py collectstatic --noinput"
        ;;
esac

# Verificar configuración
echo ""
echo -e "${BLUE}🔍 Verificando configuración...${NC}"

# Exportar la variable de entorno para la verificación
export DJANGO_ENVIRONMENT=$ENVIRONMENT

# Verificar que Django puede cargar la configuración
if python -c "import django; django.setup()" 2>/dev/null; then
    echo -e "${GREEN}✅ Configuración de Django válida${NC}"
else
    echo -e "${RED}❌ Error en la configuración de Django${NC}"
    echo "Revisa el archivo $ENV_FILE y asegúrate de que todas las variables estén configuradas"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Entorno $ENVIRONMENT configurado correctamente${NC}"

# Instrucciones finales
if [ "$ENVIRONMENT" != "development" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Recuerda:${NC}"
    echo "  1. Configurar las variables de entorno en $ENV_FILE"
    echo "  2. Verificar la configuración de base de datos"
    echo "  3. Configurar los servicios externos (Redis, Email, etc.)"
    echo "  4. Ejecutar las migraciones si es necesario"
fi
