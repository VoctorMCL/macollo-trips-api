from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExemplarMatch(BaseModel):
    filename: str = Field(..., description="Nombre del archivo de referencia coincidente")
    stage: str = Field(..., description="Estadio biológico de la foto de referencia")
    similarity: float = Field(..., description="Similitud de cosenos normalizada (0.0 a 1.0)")

class CycleInfo(BaseModel):
    temperature_c: float = Field(..., description="Temperatura ambiente considerada (°C)")
    detected_stage_key: str = Field(..., description="Identificador del estadio")
    detected_stage_name: str = Field(..., description="Nombre agronómico del estadio detectado")
    current_stage_duration_days: str = Field(..., description="Duración estimada del estadio actual")
    days_to_adult: str = Field(..., description="Días estimados para alcanzar el estadio adulto")
    urgency_level: str = Field(..., description="Nivel de urgencia fitosanitaria (BAJO, MODERADO, ALTO, CRÍTICO)")
    urgency_rationale: str = Field(..., description="Explicación agronómica del nivel de riesgo en Gulupa")

class AgronomicRecommendations(BaseModel):
    biological_control: List[str] = Field(..., description="Acciones de control biológico con parasitoides/depredadores")
    ethological_control: List[str] = Field(..., description="Trampas cromotrópicas y atrayentes")
    cultural_control: List[str] = Field(..., description="Manejo de podas, mallas, deshierbe y monitoreo")
    chemical_biorational_control: List[str] = Field(..., description="Biorracionales, extractos y productos químicos con rotación IRAC")
    export_impact_alert: str = Field(..., description="Advertencia sobre daño en floración y frutos de Gulupa para exportación")

class PredictionResponse(BaseModel):
    is_thrips: bool = Field(..., description="Indica si se confirmó la presencia de trips o daño directo de trips")
    thrips_confidence: float = Field(..., description="Confianza global de detección (0.0 a 1.0)")
    detected_target: str = Field(..., description="Especie o categoría identificada")
    detected_stage: str = Field(..., description="Estadio biológico o manifestación de daño")
    stage_confidence: float = Field(..., description="Confianza en la clasificación del estadio (0.0 a 1.0)")
    is_damage_manifestation: bool = Field(False, description="True si la detección corresponde a daño en fruto/flor")
    cycle_info: Optional[CycleInfo] = Field(None, description="Información de desarrollo biológico y días de ciclo")
    recommendations: Optional[AgronomicRecommendations] = Field(None, description="Recomendaciones de manejo integrado de plagas (MIP)")
    exemplar_matches: List[ExemplarMatch] = Field(default_factory=list, description="Coincidencias con fotos de la galería de referencia")
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Métricas técnicas de inferencia (logits, tiempos)")
    inference_time_ms: float = Field(..., description="Tiempo total de inferencia en milisegundos")

class GalleryItem(BaseModel):
    filename: str
    stage: str
    relative_path: str
    file_size_bytes: int

class GalleryStatusResponse(BaseModel):
    total_images: int
    by_stage: Dict[str, int]
    is_indexed: bool
    index_path: str
