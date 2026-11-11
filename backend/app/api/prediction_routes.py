"""Endpoint principal de inferencia fitosanitaria."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from backend.app.auth import require_api_access
from backend.app.config import (
    DEFAULT_PROFILE,
    DEFAULT_TEMPERATURE_C,
    MODEL_RETRY_AFTER_SECONDS,
)
from backend.app.domain.catalog import get_profile
from backend.app.ml.bioclip_engine import bioclip_engine
from backend.app.schemas import PredictionResponse
from backend.app.services.images import read_image_upload

router = APIRouter(tags=["Inferencia"])


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(..., description="Foto tomada con cámara o subida desde galería"),
    temperature_c: Optional[float] = Form(
        DEFAULT_TEMPERATURE_C,
        description="Temperatura ambiental del invernadero (°C), ej. de SIATA u Open-Meteo",
    ),
    crop: Optional[str] = Form("gulupa", description="Cultivo analizado (default: gulupa)"),
    profile: Optional[str] = Form(
        DEFAULT_PROFILE,
        description="Perfil de detección: trips, moscas, aranas_rojas (ver /api/profiles)",
    ),
    use_tta: Optional[bool] = Form(
        None, description="Activa test-time augmentation (más lento, más robusto)"
    ),
    _access: dict = Depends(require_api_access),
):
    """
    Recibe una imagen y temperatura ambiental y devuelve el diagnóstico del
    perfil seleccionado:

    - Confirma si el objetivo del perfil está presente.
    - Determina estadio biológico de la plaga detectada.
    - Estima días de ciclo/presión según temperatura.
    - Emite recomendaciones de manejo integrado.
    - Compara con la galería de referencia del predio (few-shot).

    Si el modelo todavía se está cargando (cold start de Cloud Run), responde
    **503** con ``{"status": "warming", "retry_after_seconds": N}`` y la
    cabecera ``Retry-After`` para que el cliente reintente en segundos en
    lugar de quedarse esperando minutos colgado.
    """

    try:
        selected_profile = get_profile(profile)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    _contents, image = await read_image_upload(file)

    try:
        result = await run_in_threadpool(
            bioclip_engine.predict,
            image,
            temperature_c=temperature_c if temperature_c is not None else DEFAULT_TEMPERATURE_C,
            profile_key=selected_profile.key,
            use_tta=use_tta,
            crop=crop or selected_profile.crop,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la inferencia con BioCLIP: {exc}",
        ) from exc

    return result


@router.post("/warmup")
async def warmup(_access: dict = Depends(require_api_access)):
    """Dispara la carga del modelo sin bloquear y reporta su estado.

    Diseñado para que las apps cliente "precalienten" el servicio en Cloud Run
    (por ejemplo, al abrir el escáner) y la primera foto ya encuentre el modelo
    listo. Es idempotente y responde de inmediato.
    """

    state = bioclip_engine.warmup()
    return {
        **state,
        "message": (
            "El modelo está listo para inferir."
            if state["model_loaded"]
            else "El modelo se está cargando en segundo plano; consulta /api/health."
        ),
    }
