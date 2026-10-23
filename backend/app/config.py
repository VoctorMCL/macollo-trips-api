from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
GALLERY_DIR = DATA_DIR / "reference_gallery"
GALLERY_INDEX_PATH = DATA_DIR / "gallery_embeddings.pt"
STATIC_DIR = BASE_DIR / "frontend"

# Configuración del modelo BioCLIP 2.5
BIOCLIP_MODEL_NAME = "hf-hub:imageomics/bioclip-2.5-vith14"
FALLBACK_MODEL_NAME = "hf-hub:imageomics/bioclip"  # ViT-B/16 fallback if needed

DEFAULT_TEMPERATURE_C = 20.0  # Temperatura típica de cultivo de Gulupa (18°C - 24°C)
CONFIDENCE_THRESHOLD = 0.60   # Umbral base de confirmación de trips
KNN_TOP_K = 3                 # K vecinos más cercanos para el análisis de galería

# Subdirectorios de estadios en la galería
STAGES = [
    "adulto",
    "ninfa_1",
    "ninfa_2",
    "pupa",
    "dano_gulupa"
]

class Settings(BaseModel):
    app_name: str = "Gulupa Trips BioCLIP 2.5 API"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

settings = Settings()
