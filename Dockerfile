# ==============================================================================
# Etapa 1: Compilación de la interfaz Frontend (React + Vite)
# ==============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Etapa 2: Backend Python, PyTorch (CPU) y API FastAPI
# ==============================================================================
FROM python:3.11-slim

LABEL authors="victormcl"
LABEL description="API Macollo Visión Fitosanitaria - Optimizada para Google Cloud Run"

# Variables de entorno esenciales para Python y Cloud Run
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# Instalar dependencias del sistema requeridas para Pillow, OpenCV y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar PyTorch y torchvision optimizados para CPU (ahorra gigabytes respecto a CUDA)
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Instalar el resto de dependencias de Python
COPY requirements.txt .
RUN pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Precargar los pesos neuronales de BioCLIP 2.5 en la imagen de Docker.
# Esto es CRÍTICO en Google Cloud Run para que el arranque en frío (cold start) tome 3-5 segundos
# en lugar de descargar 2.5 GB por internet cada vez que una instancia despierte o escale.
RUN python -c "import open_clip; open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip-2.5-vith14')"

# Copiar el código del backend y la estructura de datos
COPY backend/ ./backend/
COPY data/ ./data/

# Hornear en la imagen los prototipos de texto de todos los perfiles del catálogo
# y el índice de la galería de referencia. En runtime load_model() los carga del
# disco en milisegundos (ver PromptBank.load_cache) en lugar de re-codificar
# ~100 prompts con el codificador de texto en CPU, lo que ahorra decenas de
# segundos en cada arranque en frío de Cloud Run.
RUN python -c "from backend.app.ml.bioclip_engine import bioclip_engine; bioclip_engine.load_model()" \
    && python -c "from backend.app.ml.bioclip_engine import bioclip_engine; assert bioclip_engine.is_loaded, 'La precomputación de cachés falló'"

# Copiar los archivos estáticos compilados de la interfaz React desde la primera etapa
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Asegurar directorios de trabajo
RUN mkdir -p data/reference_gallery

# Exponer el puerto por defecto (Cloud Run inyectará la variable $PORT en ejecución)
EXPOSE 8080

# Iniciar Uvicorn leyendo dinámicamente la variable $PORT que inyecta Cloud Run (por defecto 8080)
# 'exec' permite que Uvicorn reciba las señales del sistema (SIGTERM/SIGINT) para un apagado limpio
CMD ["sh", "-c", "exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
