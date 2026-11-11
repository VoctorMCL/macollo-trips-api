import os
from pathlib import Path
from typing import List

from pydantic import BaseModel

from backend.app.domain.catalog import DEFAULT_PROFILE_KEY, TRIPS_STAGES

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
GALLERY_DIR = DATA_DIR / "reference_gallery"
GALLERY_INDEX_PATH = DATA_DIR / "gallery_embeddings.pt"
PROMPT_CACHE_PATH = DATA_DIR / "prompt_embeddings.pt"
API_KEYS_PATH = DATA_DIR / "api_keys.json"
AUTH_SECRET_PATH = DATA_DIR / ".auth_secret"
DIST_DIR = BASE_DIR / "frontend" / "dist"
STATIC_DIR = DIST_DIR if DIST_DIR.exists() else (BASE_DIR / "frontend")

# Autenticación (login sin registro). Cambiar por variables de entorno en producción.
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "macollo2026")
SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 7)))
SESSION_COOKIE_NAME: str = "macollo_session"
SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# CORS: orígenes permitidos separados por coma (default: "*" para integración flexible)
raw_cors = os.getenv("CORS_ORIGINS", "*").strip()
CORS_ORIGINS: List[str] = [orig.strip() for orig in raw_cors.split(",") if orig.strip()] or ["*"]

# Configuración del modelo BioCLIP 2.5
BIOCLIP_MODEL_NAME: str = "hf-hub:imageomics/bioclip-2.5-vith14"
FALLBACK_MODEL_NAME: str = "hf-hub:imageomics/bioclip"  # ViT-B/16 fallback if needed

DEFAULT_TEMPERATURE_C: float = 20.0  # Temperatura típica de cultivo de Gulupa (18°C - 24°C)
DEFAULT_PROFILE: str = os.getenv("DEFAULT_DETECTION_PROFILE", DEFAULT_PROFILE_KEY)

# ML: umbrales y calibración
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
KNN_TOP_K: int = int(os.getenv("KNN_TOP_K", "5"))
GALLERY_MIN_SIMILARITY: float = float(os.getenv("GALLERY_MIN_SIMILARITY", "0.62"))
GALLERY_MAX_BOOST: float = float(os.getenv("GALLERY_MAX_BOOST", "0.15"))
ENABLE_TTA: bool = os.getenv("ENABLE_TTA", "false").lower() == "true"

# ML: rendimiento y cold start en Cloud Run.
# TORCH_NUM_THREADS = 0 -> autodetectar la cuota real de CPU del contenedor (cgroup),
# evitando que PyTorch lance tantos hilos como núcleos tiene la máquina anfitriona
# (Cloud Run limita por cuota CFS, no por máscara de afinidad, y la sobre-suscripción
# de hilos hace la inferencia varios veces más lenta).
TORCH_NUM_THREADS: int = int(os.getenv("TORCH_NUM_THREADS", "0"))
# Cuánto espera /api/predict a que el modelo termine de cargar antes de responder
# 503 "warming" (el cliente reintenta) en lugar de colgarse minutos en el cold start.
MODEL_WAIT_SECONDS: float = float(os.getenv("MODEL_WAIT_SECONDS", "2.5"))
# Segundos sugeridos al cliente para reintentar cuando el modelo está calentando.
MODEL_RETRY_AFTER_SECONDS: int = int(os.getenv("MODEL_RETRY_AFTER_SECONDS", "5"))

# Límites de subida (bytes). 15 MB por defecto.
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))

# Fases biológicas reales del ciclo de vida de los Trips (compatibilidad 1.x).
BIOLOGICAL_STAGES: List[str] = [
    stage_key for stage_key in TRIPS_STAGES if stage_key != "dano_gulupa"
]

# Subdirectorios históricos de la galería: 4 fases + manifestación de daño.
STAGES: List[str] = list(TRIPS_STAGES.keys())


class Settings(BaseModel):
    app_name: str = "Macollo Visión Fitosanitaria API"
    version: str = "2.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
