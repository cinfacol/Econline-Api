#!/bin/bash

# Script para migrar completamente a uv
# Este script convierte tu proyecto de pip a uv

echo "🚀 Migrando proyecto Econline a uv..."

# Verificar si uv está instalado
if ! command -v uv &> /dev/null; then
    echo "❌ uv no está instalado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Crear pyproject.toml desde requirements.txt si no existe
if [ ! -f "pyproject.toml" ]; then
    echo "📝 Creando pyproject.toml desde requirements.txt..."
    cat > pyproject.toml << EOF
[project]
name = "econline-api"
version = "0.1.0"
description = "Econline API Django Application"
requires-python = ">=3.10"
dependencies = [
EOF
    
    # Agregar dependencias desde requirements.txt
    if [ -f "requirements.txt" ]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ ! $line =~ ^[[:space:]]*# ]] && [[ ! -z "${line// }" ]]; then
                echo "    \"$line\"," >> pyproject.toml
            fi
        done < requirements.txt
    fi
    
    cat >> pyproject.toml << EOF
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "black>=23.0",
    "flake8>=6.0",
    "mypy>=1.0",
]
EOF
fi

# Inicializar proyecto con uv
echo "🔧 Inicializando proyecto con uv..."
uv sync

# Crear archivo .gitignore actualizado
echo "📁 Actualizando .gitignore..."
if [ ! -f ".gitignore" ]; then
    touch .gitignore
fi

# Agregar entradas específicas de uv si no existen
grep -qxF ".venv/" .gitignore || echo ".venv/" >> .gitignore
grep -qxF "uv.lock" .gitignore || echo "uv.lock" >> .gitignore
grep -qxF ".uv-cache/" .gitignore || echo ".uv-cache/" >> .gitignore

echo "✅ Migración completada!"
echo ""
echo "📚 Comandos útiles con uv:"
echo "  uv add <package>          # Agregar una dependencia"
echo "  uv add --dev <package>    # Agregar dependencia de desarrollo"
echo "  uv remove <package>       # Remover una dependencia"
echo "  uv sync                   # Sincronizar dependencias"
echo "  uv run <command>          # Ejecutar comando en el entorno virtual"
echo "  uv pip list               # Listar paquetes instalados"
echo ""
echo "🐳 Para Docker:"
echo "  docker build -t econline-api ."
echo "  docker run econline-api"
