"""
Servidor principal FastAPI para la API de Detección de Trips con BioCLIP 2.5 en Gulupa.
Incluye endpoints de inferencia, gestión de galería de fotos de referencia y soporte CORS completo.
"""

import io
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image

from backend.app.config import (
    settings,
    GALLERY_DIR,
    STATIC_DIR,
    STAGES,
    DEFAULT_TEMPERATURE_C
)
from backend.app.ml.bioclip_engine import bioclip_engine
from backend.app.ml.gallery_index import gallery_manager
from backend.app.schemas.prediction import (
    PredictionResponse,
    GalleryStatusResponse,
    GalleryItem
)
from backend.app.agronomy.gulupa_cycle import get_gulupa_cycle_estimate
from backend.app.agronomy.gulupa_mip import get_gulupa_mip_recommendations

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{settings.app_name}] Iniciando servicio...")
    # Cargar modelo en memoria durante el arranque
    try:
        bioclip_engine.load_model()
    except Exception as e:
        print(f"[{settings.app_name}] Error precargando BioCLIP: {e}")
    yield
    print(f"[{settings.app_name}] Deteniendo servicio...")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="API de Machine Learning con BioCLIP 2.5 para identificación de trips, estadios biológicos y manejo fitosanitario en Gulupa.",
    lifespan=lifespan
)

# Configuración CORS completa para permitir llamadas desde la página web existente del usuario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoints de Salud y Estado
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Verifica el estado del servicio, modelo cargado y recursos."""
    stats = gallery_manager.get_gallery_stats()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "model_loaded": bioclip_engine.is_loaded,
        "model_name": bioclip_engine.loaded_model_name,
        "device": str(bioclip_engine.device),
        "gallery_total_images": stats["total_images"],
        "gallery_is_indexed": stats["is_indexed"],
        "server_time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

# ---------------------------------------------------------------------------
# Endpoint Principal de Inferencia
# ---------------------------------------------------------------------------

@app.post("/api/predict", response_model=PredictionResponse)
async def predict_thrips(
    file: UploadFile = File(..., description="Foto tomada con cámara o subida desde galería"),
    temperature_c: Optional[float] = Form(DEFAULT_TEMPERATURE_C, description="Temperatura ambiental del invernadero (°C), ej. de SIATA u Open-Meteo"),
    crop: Optional[str] = Form("gulupa", description="Cultivo analizado (default: gulupa)")
):
    """
    Recibe una imagen (hoja, flor, fruto o insecto) y temperatura ambiental:
    - Confirma si es un Trips frente a otros insectos u hoja sana.
    - Determina el estadio biológico (Adulto, Ninfa I, Ninfa II, Pupa, Daño).
    - Proporciona estimación de días de ciclo según grados de temperatura.
    - Emite recomendaciones fitosanitarias de Manejo Integrado de Plagas (MIP).
    - Compara con la Galería de Referencia (Few-Shot) para validar con fotos reales del predio.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo proporcionado no es una imagen válida."
        )

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo procesar la imagen enviada: {str(e)}"
        )

    # Inferencia con BioCLIP 2.5
    try:
        result = bioclip_engine.predict(image, temperature_c=temperature_c)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la inferencia con BioCLIP: {str(e)}"
        )

# ---------------------------------------------------------------------------
# Endpoints de Gestión de la Galería de Referencia (Fotos del Usuario)
# ---------------------------------------------------------------------------

@app.get("/api/gallery", response_model=GalleryStatusResponse)
async def get_gallery_status():
    """Obtiene el estado general del banco de fotos de referencia."""
    stats = gallery_manager.get_gallery_stats()
    return stats

@app.get("/api/gallery/items")
async def list_gallery_items():
    """Lista las imágenes indexadas en cada estadio con su ruta relativa."""
    return gallery_manager.list_items()

@app.post("/api/gallery/upload")
async def upload_gallery_image(
    file: UploadFile = File(..., description="Foto de referencia de trips tomada en el invernadero"),
    stage: str = Form(..., description="Estadio biológico: adulto, ninfa_1, ninfa_2, pupa, dano_gulupa")
):
    """
    Permite subir fotos reales del usuario al servidor para enriquecer el modelo BioCLIP.
    Guarda la foto en la carpeta correspondiente y reindexa el espacio de embeddings.
    """
    stage_clean = stage.strip().lower()
    if stage_clean not in STAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estadio no válido '{stage}'. Debe ser uno de: {', '.join(STAGES)}"
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo subido debe ser una imagen (JPG, PNG, WebP)."
        )

    contents = await file.read()
    # Asegurar que sea una imagen válida
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Imagen no válida: {e}")

    # Guardar en disco
    target_dir = GALLERY_DIR / stage_clean
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo seguro
    clean_name = Path(file.filename).name.replace(" ", "_")
    target_path = target_dir / f"{int(time.time())}_{clean_name}"
    
    with open(target_path, "wb") as f:
        f.write(contents)

    # Reindexar galería
    if bioclip_engine.is_loaded:
        indexed_count = gallery_manager.rebuild_index(
            bioclip_engine.model,
            bioclip_engine.preprocess,
            bioclip_engine.device
        )
    else:
        indexed_count = 0

    return {
        "message": f"Imagen guardada exitosamente en estadio '{stage_clean}'.",
        "filename": target_path.name,
        "stage": stage_clean,
        "total_indexed_images": indexed_count
    }

@app.post("/api/gallery/reindex")
async def reindex_gallery():
    """Fuerza la reindexación de todas las imágenes colocadas manualmente en las carpetas locales."""
    if not bioclip_engine.is_loaded:
        bioclip_engine.load_model()

    count = gallery_manager.rebuild_index(
        bioclip_engine.model,
        bioclip_engine.preprocess,
        bioclip_engine.device
    )
    return {
        "message": "Reindexación completada exitosamente.",
        "indexed_images": count,
        "stats": gallery_manager.get_gallery_stats()
    }

# ---------------------------------------------------------------------------
# Endpoint de Información y Manual de Campo para Gulupa
# ---------------------------------------------------------------------------

@app.get("/api/gulupa-handbook")
async def get_gulupa_handbook(temperature_c: float = 20.0):
    """Devuelve la guía técnica completa de trips en Gulupa según temperatura."""
    return {
        "crop": "Gulupa (Passiflora edulis f. edulis)",
        "key_thrips_species": [
            {"scientific_name": "Frankliniella occidentalis", "common_name": "Trips de las flores (vector principal)"},
            {"scientific_name": "Frankliniella panamensis", "common_name": "Trips de las pasifloras"},
            {"scientific_name": "Thrips tabaci", "common_name": "Trips de la cebolla / polífago"}
        ],
        "economic_damage_manifestation": "Cacarizado o roña corchosa en la cáscara de frutos tiernos y caída prematura de botones florales.",
        "sample_cycle_estimate_at_temp": get_gulupa_cycle_estimate("adulto", temperature_c),
        "sample_recommendations": get_gulupa_mip_recommendations("adulto")
    }

# ---------------------------------------------------------------------------
# Montaje del Frontend Web App Móvil
# ---------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
