"""Registro de proveedores agronómicos por perfil de detección."""

from typing import Any, Dict, Optional, Tuple

from backend.app.agronomy.flies import (
    get_fly_cycle_estimate,
    get_fly_mip_recommendations,
)
from backend.app.agronomy.gulupa_cycle import get_gulupa_cycle_estimate
from backend.app.agronomy.gulupa_mip import get_gulupa_mip_recommendations
from backend.app.agronomy.mites import (
    get_mite_cycle_estimate,
    get_mite_mip_recommendations,
)


def get_agronomy(
    profile_key: str,
    stage_key: str,
    temperature_c: float,
    target_key: Optional[str] = None,
    is_damage_only: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Devuelve ``(cycle_info, recommendations)`` para el perfil solicitado."""

    if profile_key == "trips":
        cycle = get_gulupa_cycle_estimate(stage_key, temperature_c)
        recommendations = get_gulupa_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        cycle.setdefault("profile", "trips")
        return cycle, recommendations

    if profile_key == "moscas":
        cycle = get_fly_cycle_estimate(stage_key, temperature_c)
        recommendations = get_fly_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        return cycle, recommendations

    if profile_key == "aranas_rojas":
        cycle = get_mite_cycle_estimate(stage_key, temperature_c)
        recommendations = get_mite_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        return cycle, recommendations

    return None, None
