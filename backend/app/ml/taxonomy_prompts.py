"""
Prompts taxonómicos y de estadios del perfil Trips.

Este módulo se conserva por compatibilidad con la API pública de la versión 1.x.
La fuente de verdad es ``backend.app.domain.catalog``, que permite añadir nuevos
perfiles (moscas, arañas rojas) sin modificar el motor de inferencia.
"""

from typing import Dict

from backend.app.domain.catalog import (
    TARGETS,
    TRIPS_PROFILE,
    TRIPS_STAGES,
    get_target,
)

# Claves positivas del perfil Trips (se mantiene el nombre histórico).
POSITIVE_TRIPS_KEYS = list(TRIPS_PROFILE.positive_target_keys)

# Prompts principales por objetivo (se usa el primer prompt de cada target).
TAXONOMIC_TARGET_PROMPTS: Dict[str, str] = {
    key: TARGETS[key].prompts[0]
    for key in TRIPS_PROFILE.target_keys
}

# Prompts de estadios biológicos con el formato histórico.
BIOLOGICAL_STAGE_PROMPTS: Dict[str, Dict[str, str]] = {
    key: {
        "name": stage.name,
        "description": stage.description,
        "prompt": stage.prompts[0],
    }
    for key, stage in TRIPS_STAGES.items()
}


def get_target_prompts(target_key: str) -> tuple:
    """Devuelve todos los prompts (ensamble) de un objetivo del catálogo."""

    return get_target(target_key).prompts


__all__ = [
    "TAXONOMIC_TARGET_PROMPTS",
    "BIOLOGICAL_STAGE_PROMPTS",
    "POSITIVE_TRIPS_KEYS",
    "get_target_prompts",
]
