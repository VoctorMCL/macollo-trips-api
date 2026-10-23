#!/usr/bin/env bash
set -e

# Script de arranque para la API de Trips BioCLIP 2.5 en Gulupa
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "🌱 Iniciando Servidor BioCLIP 2.5 — Trips en Gulupa"
echo "=========================================================="

# Activar entorno virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ Entorno .venv no encontrado. Ejecutando con python3 del sistema..."
fi

# Detectar IP local para facilitar acceso desde el celular en el invernadero
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo "🚀 Servidor escuchando en:"
echo "   - Local:      http://localhost:8000"
echo "   - Red Wi-Fi:  http://${LOCAL_IP}:8000  (Usa esta URL desde tu celular en el invernadero)"
echo "   - Docs API:   http://localhost:8000/docs"
echo "=========================================================="

exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
