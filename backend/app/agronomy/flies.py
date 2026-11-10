"""
Modelo térmico y recomendaciones MIP para moscas de la fruta (Anastrepha spp.).

Perfil ``moscas`` del catálogo. Los parámetros son orientativos y deben
calibrarse con la temperatura real del invernadero y la galería del predio.
"""

from typing import Any, Dict, List

T_BASE = 10.0  # °C

THERMAL_REQUIREMENTS_GDD = {
    "huevo": 45.0,
    "larva": 110.0,
    "pupa": 180.0,
}


def _stage_days(gdd: float, temperature_c: float) -> float:
    effective_temp = max(temperature_c - T_BASE, 1.5)
    return max(1.5, min(gdd / effective_temp, 40.0))


def get_fly_cycle_estimate(stage_key: str, temperature_c: float = 20.0) -> Dict[str, Any]:
    """Estima la duración del ciclo de la mosca de la fruta según la temperatura."""

    temp = max(12.0, min(temperature_c, 34.0))
    days_egg = _stage_days(THERMAL_REQUIREMENTS_GDD["huevo"], temp)
    days_larva = _stage_days(THERMAL_REQUIREMENTS_GDD["larva"], temp)
    days_pupa = _stage_days(THERMAL_REQUIREMENTS_GDD["pupa"], temp)

    info: Dict[str, Any] = {
        "profile": "moscas",
        "temperature_c": round(temp, 1),
        "detected_stage_key": stage_key,
        "detected_stage_name": "Monitoreo general de mosca de la fruta",
        "current_stage_duration_days": (
            f"Ciclo completo huevo-adulto: ~{round(days_egg + days_larva + days_pupa, 1)} "
            f"días a {temp}°C"
        ),
        "days_to_adult": "Monitoreo preventivo con trampas y revisión de frutos",
        "urgency_level": "MODERADO",
        "urgency_rationale": (
            "La mosca de la fruta se detecta mejor con trampas con atrayente y revisión "
            "de frutos en maduración. Mantén el monitoreo semanal y retira frutos caídos."
        ),
    }

    if stage_key == "huevo":
        info.update(
            {
                "detected_stage_name": "Huevo (Incubación en el Fruto)",
                "current_stage_duration_days": f"{round(days_egg, 1)} días a {temp}°C",
                "days_to_adult": (
                    f"{round(days_larva + days_pupa, 1)} días para la siguiente generación"
                ),
                "urgency_level": "ALTO",
                "urgency_rationale": (
                    "Los huevos están protegidos bajo la epidermis del fruto. Revisa "
                    "picaduras de oviposición y refuerza el trampeo."
                ),
            }
        )
    elif stage_key == "larva":
        info.update(
            {
                "detected_stage_name": "Larva (Fase de Daño en Pulpa)",
                "current_stage_duration_days": f"{round(days_larva, 1)} días a {temp}°C",
                "days_to_adult": f"{round(days_pupa, 1)} días para la emergencia de adultos",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "La larva consume la pulpa y abre la puerta a pudriciones. Retira y "
                    "destruye frutos afectados; no los dejes en el suelo."
                ),
            }
        )
    elif stage_key == "pupa":
        info.update(
            {
                "detected_stage_name": "Pupa (Fase Críptica en Suelo)",
                "current_stage_duration_days": f"{round(days_pupa, 1)} días a {temp}°C",
                "days_to_adult": "Emergencia de adultos desde suelo o frutos caídos",
                "urgency_level": "ALTO",
                "urgency_rationale": (
                    "La pupa suele estar en el suelo o en frutos caídos. La limpieza del "
                    "plateo y el control biológico de suelo reducen la emergencia."
                ),
            }
        )
    elif stage_key == "adulto":
        info.update(
            {
                "detected_stage_name": "Adulto (Dispersión y Oviposición)",
                "current_stage_duration_days": (
                    f"Longevidad aproximada: {round(60 / max(temp - 8, 4))} a "
                    f"{round(120 / max(temp - 8, 4))} días"
                ),
                "days_to_adult": "Fase reproductora activa",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "Los adultos dispersan la plaga y ovipositan en frutos. Instala "
                    "trampas con atrayente, revisa frutos y activa el control etológico."
                ),
            }
        )
    elif stage_key == "dano":
        info.update(
            {
                "detected_stage_name": "Daño por Mosca de la Fruta",
                "current_stage_duration_days": "Lesión acumulativa en el fruto",
                "days_to_adult": "Revisa focos y frutos caídos para cortar el ciclo",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "Las picaduras, la pudrición y las larvas en fruto confirman actividad "
                    "reciente. Realiza recolección sanitaria y eliminación de frutos afectados."
                ),
            }
        )

    return info


def get_fly_mip_recommendations(
    stage_key: str, is_damage_only: bool = False
) -> Dict[str, Any]:
    """Recomendaciones de manejo integrado para mosca de la fruta."""

    biological: List[str] = [
        "Conservación de parasitoides de pupario (Diachasmimorpha longicaudata, Aganaspis daci) en el entorno.",
        "Aplicación de Beauveria bassiana o Metarhizium anisopliae en el suelo bajo la copa para pupas.",
        "Uso de nematodos entomopatógenos Steinernema feltiae en el plateo y frutos caídos.",
        "Evita insecticidas de amplio espectro que eliminen la fauna benéfica del huerto.",
    ]
    ethological: List[str] = [
        "Trampeo masivo con atrayentes alimenticios (proteína hidrolizada o cebos autorizados).",
        "Densidad de monitoreo: 1 trampa cada 20-30 m²; aumentar en bordes y focos.",
        "Revisión semanal de 20 frutos en maduración y conteo de picaduras de oviposición.",
        "Mallas anti-insectos de al menos 50 mesh en ventanas y doble puerta de acceso.",
    ]
    cultural: List[str] = [
        "Recolección diaria o semanal de frutos caídos y destrucción fuera del lote.",
        "Poda de ventilación y manejo de humedad para reducir refugios húmedos.",
        "Eliminación de hospederos alternos en el perímetro del invernadero.",
        "Desinfección de calzado, herramientas, canastillas y bandejas al ingresar.",
    ]
    chemical: List[str] = [
        "Priorizar trampeo masivo y cebos autorizados antes que insecticidas de contacto.",
        "Biorracional a base de azadiractina o aceite mineral como apoyo, respetando abejas.",
        "Rotación de modos de acción IRAC y respeto de los periodos de carencia para exportación.",
        "No aplicar insecticidas de contacto sobre frutos listos para cosecha.",
    ]
    if is_damage_only or stage_key == "dano":
        cultural.insert(
            0,
            "Separa y destruye frutos con picaduras o larvas; no los dejes en el suelo ni en la planta.",
        )

    return {
        "biological_control": biological,
        "ethological_control": ethological,
        "cultural_control": cultural,
        "chemical_biorational_control": chemical,
        "export_impact_alert": (
            "ALERTA DE EXPORTACIÓN: la presencia de larvas o picaduras de mosca de la fruta "
            "puede causar rechazo cuarentenario. Mantén trampeo, eliminación de frutos y "
            "trazabilidad por lote."
        ),
    }
