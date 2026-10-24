"""
Servidor principal FastAPI para la API de Detección de Trips con BioCLIP 2.5 en Gulupa.
Incluye endpoints de inferencia, gestión de galería de fotos de referencia y soporte CORS completo.
"""

import io
import re
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, UploadFile, File, Form, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from backend.app.config import (
    settings,
    GALLERY_DIR,
    STATIC_DIR,
    STAGES,
    DEFAULT_TEMPERATURE_C,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_SECONDS,
    CORS_ORIGINS,
)
from backend.app.auth import (
    authenticate_admin,
    create_api_key,
    create_session_token,
    list_api_keys,
    require_api_access,
    require_session,
    revoke_api_key,
)
from backend.app.ml.bioclip_engine import bioclip_engine
from backend.app.ml.gallery_index import gallery_manager
from backend.app.schemas import (
    PredictionResponse,
    GalleryStatusResponse,
    LoginRequest,
    ApiKeyCreateRequest,
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
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def disable_ui_cache(request, call_next):
    """Evita que el navegador conserve HTML/CSS/JS viejos del panel."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith(("/css/", "/js/", "/assets/")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

# ---------------------------------------------------------------------------
# Autenticación del Panel (login sin registro público)
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
async def login(payload: LoginRequest, response: Response):
    """Inicia sesión con las credenciales del administrador configuradas en el servidor."""
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )

    token = create_session_token(payload.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
    )
    return {"authenticated": True, "username": payload.username}

@app.post("/api/auth/logout")
async def logout(response: Response):
    """Cierra la sesión del panel."""
    response.delete_cookie(SESSION_COOKIE_NAME, secure=SESSION_COOKIE_SECURE, samesite="lax")
    return {"authenticated": False}

@app.get("/api/auth/me")
async def auth_me(username: str = Depends(require_session)):
    """Devuelve el usuario autenticado actual."""
    return {"authenticated": True, "username": username}

# ---------------------------------------------------------------------------
# Gestión de API Keys (solo usuarios autenticados en el panel)
# ---------------------------------------------------------------------------

@app.get("/api/keys")
async def get_api_keys(_username: str = Depends(require_session)):
    """Lista las claves de API emitidas (sin mostrar la clave completa)."""
    return {"items": list_api_keys()}

@app.post("/api/keys")
async def create_new_api_key(
    payload: ApiKeyCreateRequest,
    username: str = Depends(require_session)
):
    """Genera una nueva API key. La clave completa solo se muestra una vez."""
    created = create_api_key(payload.name, username)
    return {
        "message": "API key creada. Guárdala ahora: no se volverá a mostrar.",
        "raw_key": created["raw_key"],
        "key": created["key"],
    }

@app.delete("/api/keys/{key_id}")
async def delete_api_key(key_id: str, _username: str = Depends(require_session)):
    """Revoca una API key existente."""
    if not revoke_api_key(key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key no encontrada.")
    return {"message": "API key revocada correctamente."}

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
    crop: Optional[str] = Form("gulupa", description="Cultivo analizado (default: gulupa)"),
    _access: dict = Depends(require_api_access)
):
    """
    Recibe una imagen (hoja, flor, fruto o insecto) y temperatura ambiental:
    - Confirma si es un Trips frente a otros insectos u hoja sana.
    - Determina el estadio biológico (Huevo, Larva/Ninfa, Pupa, Adulto) o el daño visible.
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
async def get_gallery_status(_username: str = Depends(require_session)):
    """Obtiene el estado general del banco de fotos de referencia."""
    stats = gallery_manager.get_gallery_stats()
    return stats

@app.get("/api/gallery/items")
async def list_gallery_items(_username: str = Depends(require_session)):
    """Lista las imágenes indexadas en cada estadio con su ruta relativa."""
    return gallery_manager.list_items()

@app.post("/api/gallery/upload")
async def upload_gallery_image(
    file: UploadFile = File(..., description="Foto de referencia de trips tomada en el invernadero"),
    stage: str = Form(..., description="Estadio biológico: huevo, larva, pupa, adulto, dano_gulupa"),
    _username: str = Depends(require_session)
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

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    raw_filename = file.filename or "muestra.jpg"
    ext = Path(raw_filename).suffix.lower()
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida ('{ext}'). Extensiones aceptadas: {', '.join(sorted(valid_extensions))}"
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo subido debe ser una imagen (JPG, PNG, WebP)."
        )

    contents = await file.read()
    # Asegurar que sea una imagen válida
    try:
        Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Imagen no válida: {e}")

    # Guardar en disco
    target_dir = GALLERY_DIR / stage_clean
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo seguro sin caracteres especiales ni secuencias de escape
    clean_base = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(raw_filename).name)
    target_path = target_dir / f"{int(time.time())}_{clean_base}"
    
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
async def reindex_gallery(_username: str = Depends(require_session)):
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
async def get_gulupa_handbook(
    temperature_c: float = 20.0,
    _access: dict = Depends(require_api_access)
):
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
