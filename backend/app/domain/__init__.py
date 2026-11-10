"""Dominio agronómico: catálogo de perfiles, objetivos y estadios de detección."""

from backend.app.domain.catalog import (
    DEFAULT_PROFILE_KEY,
    GALLERY_LABELS,
    PROFILES,
    DetectionProfile,
    DetectionTarget,
    GalleryLabel,
    StageDefinition,
    build_gallery_label_key,
    get_gallery_label,
    get_profile,
    get_target,
    list_gallery_labels,
    list_profiles,
)

__all__ = [
    "DEFAULT_PROFILE_KEY",
    "GALLERY_LABELS",
    "PROFILES",
    "DetectionProfile",
    "DetectionTarget",
    "GalleryLabel",
    "StageDefinition",
    "build_gallery_label_key",
    "get_gallery_label",
    "get_profile",
    "get_target",
    "list_gallery_labels",
    "list_profiles",
]
