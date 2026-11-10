"""
Modelo térmico y recomendaciones MIP para araña roja (Tetranychus urticae).

Los parámetros son orientativos para el perfil ``aranas_rojas`` y deben
calibrarse con la temperatura real del invernadero y las fotos de la galería.
"""

from typing import Any, Dict, List

T_BASE = 10.5  # °C

THERMAL_REQUIREMENTS_GDD = {
    "huevo": 70.0,
    "larva": 80.0,
    "pupa": 0.0,  # los ácaros no tienen pupa; se mantiene por compatibilidad
    "adulto": 0.0,
}


def _stage_days(gdd: float, temperature_c: float) -> float:
    effective_temp = max(temperature_c - T_BASE, 1.5)
    return max(1.5, min(gdd / effective_temp, 40.0))


def get_mite_cycle_estimate(
    stage_key: str, temperature_c: float = 20.0
) -> Dict[str, Any]:
    """Estima la duración del ciclo de la araña roja según la temperatura."""

    temp = max(12.0, min(temperature_c, 36.0))
    days_egg = _stage_days(THERMAL_REQUIREMENTS_GDD["huevo"], temp)
    days_larva = _stage_days(THERMAL_REQUIREMENTS_GDD["larva"], temp)
    total = days_egg + days_larva

    info: Dict[str, Any] = {
        "profile": "aranas_rojas",
        "temperature_c": round(temp, 1),
        "detected_stage_key": stage_key,
        "detected_stage_name": "Monitoreo general de araña roja",
        "current_stage_duration_days": (
            f"Huevo a adulto: ~{round(total, 1)} días a {temp}°C"
        ),
        "days_to_adult": "Revisa el envés y los focos secos",
        "urgency_level": "MODERADO",
        "urgency_rationale": (
            "La araña roja se multiplica más rápido con calor y baja humedad. "
            "Monitorea el envés de hojas del tercio medio y los bordes del lote."
        ),
    }

    if stage_key == "huevo":
        info.update(
            {
                "detected_stage_name": "Huevo (Incubación)",
                "current_stage_duration_days": f"{round(days_egg, 1)} días a {temp}°C",
                "days_to_adult": (
                    f"{round(days_larva, 1)} días para completar el desarrollo tras la eclosión"
                ),
                "urgency_level": "ALTO",
                "urgency_rationale": (
                    "Los huevos están agrupados junto a las nervaduras. Una generación "
                    "adicional puede aparecer en pocos días si el ambiente es cálido y seco."
                ),
            }
        )
    elif stage_key == "larva":
        info.update(
            {
                "detected_stage_name": "Ninfa (Fase de Alimentación)",
                "current_stage_duration_days": f"{round(days_larva, 1)} días a {temp}°C",
                "days_to_adult": "Fase móvil; aplica control dirigido al envés",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "Las ninfas se alimentan activamente y generan punteado clorótico. "
                    "Interviene antes de que aparezca telaraña densa y defoliación."
                ),
            }
        )
    elif stage_key == "adulto":
        info.update(
            {
                "detected_stage_name": "Adulto (Reproducción y Dispersión)",
                "current_stage_duration_days": (
                    f"Longevidad aproximada: {round(120 / max(temp - 8, 4))} a "
                    f"{round(220 / max(temp - 8, 4))} días"
                ),
                "days_to_adult": "Fase reproductora activa",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "Los adultos ovipositan y se dispersan por viento, ropa y herramientas. "
                    "Refuerza focos, revisa bordes y activa control biológico."
                ),
            }
        )
    elif stage_key == "dano":
        info.update(
            {
                "detected_stage_name": "Daño por Araña Roja (Telaraña / Punteado)",
                "current_stage_duration_days": "Lesión acumulativa en la hoja",
                "days_to_adult": "Revisa focos y brotes nuevos para cortar el ciclo",
                "urgency_level": "CRÍTICO",
                "urgency_rationale": (
                    "El punteado amarillo, el bronceado y la telaraña confirman una "
                    "colonización establecida. Realiza poda sanitaria y trata el envés."
                ),
            }
        )

    return info


def get_mite_mip_recommendations(
    stage_key: str, is_damage_only: bool = False
) -> Dict[str, Any]:
    """Recomendaciones de manejo integrado para araña roja."""

    biological: List[str] = [
        "Liberación de Phytoseiulus persimilis (2-5 ind/m²) en focos con telaraña y humedad relativa alta.",
        "Uso de Neoseiulus californicus o Amblyseius swirskii (1-3 ind/m²) para prevención en épocas cálidas.",
        "Aplicación de Beauveria bassiana al atardecer, dirigida al envés de las hojas.",
        "Conservación de depredadores nativos: evita insecticidas de amplio espectro y respeta los bordes del lote.",
    ]
    ethological: List[str] = [
        "Monitoreo semanal del envés: 20 hojas del tercio medio y 10 brotes por lote.",
        "Revisión de focos secos, polvorientos y bordes del invernadero, donde la araña roja inicia.",
        "Uso de lupa de mano o macro para confirmar huevos, ninfas, adultos y telaraña.",
        "Registro de temperatura y humedad relativa: calor y HR baja aceleran el ciclo.",
    ]
    cultural: List[str] = [
        "Aumentar la humedad relativa y evitar ambientes polvorientos alrededor del cultivo.",
        "Eliminar malezas hospederas y restos de poda del perímetro del invernadero.",
        "Evitar exceso de nitrógeno, que favorece brotes tiernos y poblaciones de ácaros.",
        "Poda sanitaria de hojas muy afectadas y retiro del material del lote.",
    ]
    chemical: List[str] = [
        "Jabón potásico 3-5 cc/L + aceite mineral parafínico dirigido al envés, respetando fauna benéfica.",
        "Azadiractina 1% o extractos botánicos como apoyo biorracional en estados inmaduros.",
        "Rotar modos de acción IRAC: abamectina (IRAC 6), spiromesifen (IRAC 23) o bifenazate (IRAC 20D).",
        "No repetir el mismo grupo IRAC en aplicaciones consecutivas; alternar con control biológico.",
    ]
    if is_damage_only or stage_key == "dano":
        cultural.insert(
            0,
            "Retira y destruye hojas con telaraña densa para reducir la fuente de inóculo.",
        )

    return {
        "biological_control": biological,
        "ethological_control": ethological,
        "cultural_control": cultural,
        "chemical_biorational_control": chemical,
        "export_impact_alert": (
            "ALERTA DE CALIDAD: el punteado y bronceado por araña roja reduce el valor "
            "comercial de la fruta y la capacidad fotosintética. Mantén el monitoreo del "
            "envés y evita que los focos lleguen a telaraña densa."
        ),
    }
