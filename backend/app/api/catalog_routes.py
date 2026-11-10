"""Catálogo de perfiles, objetivos, estadios y fichas técnicas."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.agronomy.registry import get_agronomy
from backend.app.auth import require_api_access
from backend.app.domain.catalog import (
    DEFAULT_PROFILE_KEY,
    DetectionProfile,
    get_profile,
    get_target,
    list_profiles,
)
from backend.app.schemas import (
    CatalogResponse,
    ProfileInfo,
    StageInfo,
    TargetInfo,
)

router = APIRouter(tags=["Catálogo"])


def profile_to_info(profile: DetectionProfile) -> Dict[str, Any]:
    targets: List[TargetInfo] = []
    for key in profile.target_keys:
        target = get_target(key)
        targets.append(
            TargetInfo(
                key=target.key,
                common_name=target.common_name,
                scientific_name=target.scientific_name,
                kind=target.kind,
                description=target.description,
                is_positive=profile.is_positive_target(key),
            )
        )

    stages = [
        StageInfo(key=key, name=stage.name, description=stage.description)
        for key, stage in profile.stages.items()
    ]

    return ProfileInfo(
        key=profile.key,
        name=profile.name,
        description=profile.description,
        crop=profile.crop,
        experimental=profile.experimental,
        targets=targets,
        stages=stages,
        default_confidence_threshold=profile.min_confidence,
    ).model_dump()


def profile_targets(profile: DetectionProfile):
    return [get_target(key) for key in profile.target_keys]


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog():
    """Devuelve el catálogo completo de perfiles de detección."""

    return CatalogResponse(
        default_profile=DEFAULT_PROFILE_KEY,
        profiles=[ProfileInfo(**profile_to_info(profile)) for profile in list_profiles()],
    )


@router.get("/profiles", response_model=List[ProfileInfo])
async def get_profiles():
    """Lista los perfiles disponibles (trips, moscas, aranas_rojas)."""

    return [ProfileInfo(**profile_to_info(profile)) for profile in list_profiles()]


@router.get("/profiles/{profile_key}", response_model=ProfileInfo)
async def get_profile_detail(profile_key: str):
    """Detalle de un perfil: objetivos, estadios y umbrales."""

    try:
        profile = get_profile(profile_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ProfileInfo(**profile_to_info(profile))


def _sample_stage_key(profile: DetectionProfile) -> str:
    if "adulto" in profile.stages:
        return "adulto"
    if profile.stages:
        return next(iter(profile.stages))
    return ""


@router.get("/handbook")
async def get_handbook(
    profile: str = Query(DEFAULT_PROFILE_KEY, description="Perfil de detección"),
    temperature_c: float = Query(20.0, description="Temperatura ambiental (°C)"),
    _access: dict = Depends(require_api_access),
):
    """Ficha técnica genérica y recomendaciones de ejemplo para un perfil."""

    try:
        selected = get_profile(profile)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    stage_key = _sample_stage_key(selected)
    target_key = selected.positive_target_keys[0] if selected.positive_target_keys else None
    cycle_info, recommendations = get_agronomy(
        profile_key=selected.key,
        stage_key=stage_key,
        temperature_c=temperature_c,
        target_key=target_key,
        is_damage_only=False,
    )

    info = profile_to_info(selected)
    return {
        "profile": info,
        "crop": selected.crop,
        "sample_cycle_estimate_at_temp": cycle_info,
        "sample_recommendations": recommendations,
    }


@router.get("/gulupa-handbook")
async def get_gulupa_handbook(
    temperature_c: float = 20.0,
    _access: dict = Depends(require_api_access),
):
    """Ficha técnica histórica de trips en Gulupa (compatibilidad 1.x)."""

    profile = get_profile("trips")
    stage_key = "adulto"
    cycle_info, recommendations = get_agronomy(
        profile_key="trips",
        stage_key=stage_key,
        temperature_c=temperature_c,
        target_key="trips_general",
        is_damage_only=False,
    )

    species = [
        {
            "scientific_name": target.scientific_name,
            "common_name": target.common_name,
        }
        for target in profile_targets(profile)
        if target.kind == "pest"
    ]
    damage_target = next(
        (target for target in profile_targets(profile) if target.kind == "damage"),
        None,
    )

    return {
        "crop": "Gulupa (Passiflora edulis f. edulis)",
        "profile": profile_to_info(profile),
        "key_thrips_species": species,
        "economic_damage_manifestation": (
            damage_target.description if damage_target else "Daño foliar y de fruto."
        ),
        "sample_cycle_estimate_at_temp": cycle_info,
        "sample_recommendations": recommendations,
    }
