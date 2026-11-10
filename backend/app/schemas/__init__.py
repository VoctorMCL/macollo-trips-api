"""
Módulo de esquemas Pydantic para validación y serialización de datos de la API.
"""

from backend.app.schemas.prediction import (
    ExemplarMatch,
    CycleInfo,
    AgronomicRecommendations,
    TargetInfo,
    StageInfo,
    DetectionInfo,
    PredictionResponse,
    GalleryItem,
    GalleryStatusResponse,
    GalleryLabelInfo,
    GalleryLabelsResponse,
    ProfileInfo,
    CatalogResponse,
)
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ApiKeyCreateRequest,
    ApiKeyPublic,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
)

__all__ = [
    "ExemplarMatch",
    "CycleInfo",
    "AgronomicRecommendations",
    "TargetInfo",
    "StageInfo",
    "DetectionInfo",
    "PredictionResponse",
    "GalleryItem",
    "GalleryStatusResponse",
    "GalleryLabelInfo",
    "GalleryLabelsResponse",
    "ProfileInfo",
    "CatalogResponse",
    "LoginRequest",
    "LoginResponse",
    "ApiKeyCreateRequest",
    "ApiKeyPublic",
    "ApiKeyCreateResponse",
    "ApiKeyListResponse",
]
