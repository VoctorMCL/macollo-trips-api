"""Rutas de gestión de la galería de referencia few-shot."""

import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from backend.app.auth import require_session
from backend.app.config import GALLERY_DIR, STAGES
from backend.app.domain.catalog import (
    TRIPS_STAGES,
    GalleryLabel,
    build_gallery_label_key,
    get_gallery_label,
    get_profile,
    list_gallery_labels,
)
from backend.app.ml.bioclip_engine import bioclip_engine
from backend.app.ml.gallery_index import gallery_manager
from backend.app.schemas import (
    GalleryLabelInfo,
    GalleryLabelsResponse,
    GalleryStatusResponse,
)
from backend.app.services.images import (
    read_image_upload,
    sanitize_filename,
    validate_extension,
)

router = APIRouter(tags=["Galería"])


@router.get("/gallery", response_model=GalleryStatusResponse)
async def get_gallery_status(_username: str = Depends(require_session)):
    """Estado general del banco de fotos de referencia."""

    return gallery_manager.get_gallery_stats()


@router.get("/gallery/items")
async def list_gallery_items(_username: str = Depends(require_session)):
    """Lista las imágenes indexadas con su perfil, objetivo y estadio."""

    return gallery_manager.list_items()


@router.get("/gallery/labels", response_model=GalleryLabelsResponse)
async def get_gallery_labels(
    profile: Optional[str] = None,
    _username: str = Depends(require_session),
):
    """Lista las carpetas de galería disponibles, agrupadas por perfil."""

    if profile:
        try:
            selected_profile = get_profile(profile).key
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
    else:
        selected_profile = None

    labels = list_gallery_labels(selected_profile)
    items = [
        GalleryLabelInfo(
            key=label.key,
            profile=label.profile,
            target=label.target,
            stage=label.stage,
            display_name=label.display_name,
        )
        for label in labels
    ]

    grouped: Dict[str, List[GalleryLabelInfo]] = {}
    for item in items:
        grouped.setdefault(item.profile, []).append(item)

    return GalleryLabelsResponse(items=items, by_profile=grouped)


def _resolve_label(
    label: Optional[str],
    profile: Optional[str],
    target: Optional[str],
    stage: Optional[str],
) -> GalleryLabel:
    """Resuelve la carpeta de galería aceptando el contrato nuevo o el histórico."""

    if label:
        try:
            return get_gallery_label(label)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

    profile_key = (profile or "trips").strip().lower()
    try:
        selected_profile = get_profile(profile_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    stage_key = (stage or "").strip().lower() or None
    target_key = (target or "").strip() or None

    if selected_profile.key == "trips" and stage_key in TRIPS_STAGES:
        return get_gallery_label(stage_key)

    if not target_key and selected_profile.positive_target_keys:
        target_key = selected_profile.positive_target_keys[0]

    if not stage_key:
        stage_key = next(iter(selected_profile.stages), None)

    try:
        label_key = build_gallery_label_key(
            selected_profile.key, target_key or "", stage_key
        )
        return get_gallery_label(label_key)
    except KeyError as exc:
        valid = ", ".join(sorted(STAGES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se pudo resolver la carpeta de galería. Usa 'label' con una "
                f"clave de /api/gallery/labels. Carpetas históricas: {valid}. "
                f"Detalle: {exc}"
            ),
        ) from exc


@router.post("/gallery/upload")
async def upload_gallery_image(
    file: UploadFile = File(..., description="Foto de referencia tomada en el invernadero"),
    label: Optional[str] = Form(
        None, description="Carpeta de galería (recomendado). Ver /api/gallery/labels"
    ),
    stage: Optional[str] = Form(
        None, description="Estadio o severidad (compatibilidad 1.x)"
    ),
    profile: Optional[str] = Form(None, description="Perfil: trips, moscas, aranas_rojas"),
    target: Optional[str] = Form(None, description="Objetivo del catálogo"),
    _username: str = Depends(require_session),
):
    """Guarda una foto de referencia y reindexa el espacio de embeddings."""

    gallery_label = _resolve_label(label, profile, target, stage)

    raw_filename = file.filename or "muestra.jpg"
    validate_extension(raw_filename)
    contents, _image = await read_image_upload(file)

    target_dir = GALLERY_DIR / gallery_label.key
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_base = sanitize_filename(raw_filename)
    target_path = target_dir / f"{int(time.time())}_{clean_base}"
    with open(target_path, "wb") as output:
        output.write(contents)

    indexed_count = 0
    if bioclip_engine.is_loaded:
        indexed_count = await run_in_threadpool(
            gallery_manager.rebuild_index,
            bioclip_engine.model,
            bioclip_engine.preprocess,
            bioclip_engine.device,
        )

    return {
        "message": (
            f"Imagen guardada exitosamente en '{gallery_label.display_name}'."
        ),
        "filename": target_path.name,
        "stage": gallery_label.stage or gallery_label.key,
        "label": gallery_label.key,
        "profile": gallery_label.profile,
        "target": gallery_label.target,
        "display_name": gallery_label.display_name,
        "indexed": bioclip_engine.is_loaded,
        "total_indexed_images": indexed_count,
    }


@router.post("/gallery/reindex")
async def reindex_gallery(_username: str = Depends(require_session)):
    """Fuerza la reindexación de todas las imágenes de la galería."""

    if not bioclip_engine.is_loaded:
        await run_in_threadpool(bioclip_engine.load_model)

    count = await run_in_threadpool(
        gallery_manager.rebuild_index,
        bioclip_engine.model,
        bioclip_engine.preprocess,
        bioclip_engine.device,
    )
    return {
        "message": "Reindexación completada exitosamente.",
        "indexed_images": count,
        "stats": gallery_manager.get_gallery_stats(),
    }
