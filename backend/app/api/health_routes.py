"""Rutas de salud y estado del servicio."""

import time

from fastapi import APIRouter

from backend.app.config import DEFAULT_PROFILE, settings
from backend.app.domain.catalog import DEFAULT_PROFILE_KEY, list_profiles
from backend.app.ml.bioclip_engine import bioclip_engine
from backend.app.ml.gallery_index import gallery_manager

router = APIRouter(tags=["Estado"])


@router.get("/health")
async def health_check():
    """Verifica el estado del servicio, modelo cargado, catálogo y galería."""

    stats = gallery_manager.get_gallery_stats()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "model_loaded": bioclip_engine.is_loaded,
        "model_name": bioclip_engine.loaded_model_name,
        "device": str(bioclip_engine.device),
        "default_profile": DEFAULT_PROFILE or DEFAULT_PROFILE_KEY,
        "profiles": [
            {"key": profile.key, "name": profile.name, "experimental": profile.experimental}
            for profile in list_profiles()
        ],
        "gallery_total_images": stats["total_images"],
        "gallery_is_indexed": stats["is_indexed"],
        "gallery_is_stale": stats.get("is_stale", False),
        "server_time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
