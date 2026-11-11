"""Utilidades compartidas para leer y validar imágenes subidas por HTTP."""

import io
import re
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError

from backend.app.config import MAX_UPLOAD_BYTES

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def sanitize_filename(raw_filename: str) -> str:
    """Evita rutas y caracteres especiales en el nombre de archivo."""

    safe_name = Path(raw_filename or "muestra.jpg").name
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", safe_name)
    return safe_name or "muestra.jpg"


def validate_extension(filename: str) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in VALID_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(VALID_IMAGE_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida ('{extension}'). Extensiones aceptadas: {allowed}",
        )
    return extension


async def read_image_upload(
    file: UploadFile,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> Tuple[bytes, Image.Image]:
    """Lee, valida y decodifica una imagen. Devuelve bytes originales y PIL RGB."""

    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo proporcionado no es una imagen válida.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )
    if len(contents) > max_bytes:
        max_mb = round(max_bytes / (1024 * 1024), 1)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La imagen supera el límite de {max_mb} MB.",
        )

    try:
        image = Image.open(io.BytesIO(contents))
        image = ImageOps.exif_transpose(image).convert("RGB")
        # Optimizar fotos gigantes de cámaras de celular (ej. 12MP-48MP):
        # BioCLIP solo requiere 224x224 o 336x336. Limitar a max 1280px ahorra
        # cientos de megabytes de RAM y acelera el preprocesamiento sin perder precisión.
        image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo procesar la imagen enviada: {exc}",
        ) from exc

    return contents, image


def check_image_quality(image: Image.Image) -> Tuple[bool, str]:
    """Verifica si la imagen tiene información visual mínima útil.

    Detecta fotos totalmente oscuras (tapa puesta, noche sin flash, dedo tapando lente),
    sobreexpuestas (completamente blancas) o sin contraste/textura (plana o desenfocada).
    """

    try:
        stat = ImageStat.Stat(image)
        channels = stat.mean[:3]
        if not channels:
            return False, "La imagen no contiene canales de color válidos."

        mean_brightness = sum(channels) / len(channels)
        total_var = sum(stat.var[:3])

        if mean_brightness < 18.0:
            return (
                False,
                "La imagen es demasiado oscura o carece de iluminación para identificar plagas.",
            )
        if mean_brightness > 245.0 and total_var < 50.0:
            return (
                False,
                "La imagen está sobreexpuesta o completamente en blanco.",
            )
        if total_var < 35.0:
            return (
                False,
                "La imagen carece de textura, nitidez o contraste reconocible.",
            )

        return True, ""
    except Exception:
        # En caso de error inesperado de cálculo, no bloquear el flujo de inferencia.
        return True, ""
