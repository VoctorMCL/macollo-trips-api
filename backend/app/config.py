import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
GALLERY_DIR = DATA_DIR / "reference_gallery"
GALLERY_INDEX_PATH = DATA_DIR / "gallery_embeddings.pt"
API_KEYS_PATH = DATA_DIR / "api_keys.json"
AUTH_SECRET_PATH = DATA_DIR / ".auth_secret"
STATIC_DIR = BASE_DIR / "frontend"

# Autenticación (login sin registro). Cambiar por variables de entorno en producción.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "macollo2026")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 24 * 7)))
SESSION_COOKIE_NAME = "macollo_session"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Configuración del modelo BioCLIP 2.5
BIOCLIP_MODEL_NAME = "hf-hub:imageomics/bioclip-2.5-vith14"
FALLBACK_MODEL_NAME = "hf-hub:imageomics/bioclip"  # ViT-B/16 fallback if needed

DEFAULT_TEMPERATURE_C = 20.0  # Temperatura típica de cultivo de Gulupa (18°C - 24°C)
CONFIDENCE_THRESHOLD = 0.60   # Umbral base de confirmación de trips
KNN_TOP_K = 3                 # K vecinos más cercanos para el análisis de galería

# Fases biológicas reales del ciclo de vida de los Trips.
# Nota: "larva" y "ninfa" son el mismo estadio (solo existe UNA fase de ninfa).
BIOLOGICAL_STAGES = [
    "huevo",
    "larva",
    "pupa",
    "adulto"
]

# Subdirectorios de la galería: las 4 fases biológicas + manifestación de daño
# (el daño no es una fase del insecto, es un síntoma para monitoreo fitosanitario).
STAGES = BIOLOGICAL_STAGES + ["dano_gulupa"]

class Settings(BaseModel):
    app_name: str = "Gulupa Trips BioCLIP 2.5 API"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

settings = Settings()
