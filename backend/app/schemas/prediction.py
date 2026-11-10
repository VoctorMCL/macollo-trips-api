from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExemplarMatch(BaseModel):
    filename: str = Field(..., description="Nombre del archivo de referencia coincidente")
    stage: str = Field(..., description="Estadio biológico o severidad de la foto de referencia")
    similarity: float = Field(..., description="Similitud de cosenos normalizada (0.0 a 1.0)")
    target: Optional[str] = Field(None, description="Objetivo del catálogo al que pertenece el ejemplar")
    profile: Optional[str] = Field(None, description="Perfil de detección del ejemplar")
    label: Optional[str] = Field(None, description="Carpeta/label de galería del ejemplar")


class CycleInfo(BaseModel):
    temperature_c: float = Field(..., description="Temperatura ambiente considerada (°C)")
    detected_stage_key: str = Field(..., description="Identificador del estadio")
    detected_stage_name: str = Field(..., description="Nombre agronómico del estadio detectado")
    current_stage_duration_days: str = Field(..., description="Duración estimada del estadio actual")
    days_to_adult: str = Field(..., description="Días estimados para la siguiente fase o ventana de riesgo")
    urgency_level: str = Field(..., description="Nivel de urgencia fitosanitaria (BAJO, MODERADO, ALTO, CRÍTICO)")
    urgency_rationale: str = Field(..., description="Explicación agronómica del nivel de riesgo")
    profile: Optional[str] = Field(None, description="Perfil de detección que generó la estimación")


class AgronomicRecommendations(BaseModel):
    biological_control: List[str] = Field(..., description="Acciones de control biológico con parasitoides/depredadores")
    ethological_control: List[str] = Field(..., description="Trampas cromotrópicas, atrayentes y monitoreo")
    cultural_control: List[str] = Field(..., description="Manejo de podas, mallas, deshierbe y monitoreo")
    chemical_biorational_control: List[str] = Field(..., description="Biorracionales, extractos y productos químicos con rotación")
    export_impact_alert: str = Field(..., description="Advertencia sobre daño en flores, frutos o pérdida de calidad")


class TargetInfo(BaseModel):
    key: str
    common_name: str
    scientific_name: Optional[str] = None
    kind: str = Field(..., description="pest, disease, damage, healthy u other")
    description: str = ""
    is_positive: bool = Field(False, description="True si es objetivo positivo del perfil")


class StageInfo(BaseModel):
    key: str
    name: str
    description: str


class DetectionInfo(BaseModel):
    profile: str = Field(..., description="Perfil de detección usado (trips, moscas, aranas_rojas)")
    profile_name: str
    category: str = Field(..., description="Categoría del objetivo detectado")
    is_positive: bool = Field(..., description="True si se detectó el objetivo del perfil")
    confidence: float = Field(..., description="Confianza calibrada (0.0 a 1.0)")
    is_uncertain: bool = Field(False, description="True si la confianza está cerca del umbral")
    target_key: str
    target_name: str
    scientific_name: Optional[str] = None
    target_description: str = ""
    profile_experimental: bool = False
    scores: Dict[str, float] = Field(default_factory=dict, description="Probabilidades por objetivo")


class PredictionResponse(BaseModel):
    # Campos históricos (compatibilidad 1.x)
    is_thrips: bool = Field(..., description="Indica si se confirmó trips (solo perfil trips)")
    thrips_confidence: float = Field(..., description="Confianza de trips (solo perfil trips)")
    detected_target: str = Field(..., description="Especie o categoría identificada")
    detected_stage: str = Field(..., description="Estadio biológico, severidad o manifestación de daño")
    stage_confidence: float = Field(..., description="Confianza en la clasificación del estadio (0.0 a 1.0)")
    is_damage_manifestation: bool = Field(False, description="True si la detección corresponde a daño")
    cycle_info: Optional[CycleInfo] = Field(None, description="Información de desarrollo biológico y días de ciclo")
    recommendations: Optional[AgronomicRecommendations] = Field(None, description="Recomendaciones de manejo integrado")
    exemplar_matches: List[ExemplarMatch] = Field(default_factory=list, description="Coincidencias con la galería de referencia")
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Métricas técnicas de inferencia")
    inference_time_ms: float = Field(..., description="Tiempo total de inferencia en milisegundos")

    # Campos genéricos (2.x): usar estos para integrar moscas, arañas y otros perfiles.
    profile: str = Field("trips", description="Perfil de detección usado")
    crop: Optional[str] = Field(None, description="Cultivo analizado")
    detection: Optional[DetectionInfo] = Field(None, description="Resultado genérico y extensible")


class GalleryItem(BaseModel):
    filename: str
    stage: str
    relative_path: str
    file_size_bytes: int
    label: Optional[str] = None
    label_key: Optional[str] = None
    target: Optional[str] = None
    profile: Optional[str] = None
    display_name: Optional[str] = None


class GalleryStatusResponse(BaseModel):
    total_images: int
    by_stage: Dict[str, int]
    by_label: Dict[str, int] = Field(default_factory=dict)
    by_profile: Dict[str, int] = Field(default_factory=dict)
    by_target: Dict[str, int] = Field(default_factory=dict)
    is_indexed: bool
    is_stale: bool = False
    indexed_images: int = 0
    index_path: str


class GalleryLabelInfo(BaseModel):
    key: str
    profile: str
    target: str
    stage: Optional[str] = None
    display_name: str


class GalleryLabelsResponse(BaseModel):
    items: List[GalleryLabelInfo] = Field(default_factory=list)
    by_profile: Dict[str, List[GalleryLabelInfo]] = Field(default_factory=dict)


class ProfileInfo(BaseModel):
    key: str
    name: str
    description: str
    crop: Optional[str] = None
    experimental: bool = False
    targets: List[TargetInfo] = Field(default_factory=list)
    stages: List[StageInfo] = Field(default_factory=list)
    default_confidence_threshold: float = 0.60


class CatalogResponse(BaseModel):
    default_profile: str
    profiles: List[ProfileInfo] = Field(default_factory=list)
