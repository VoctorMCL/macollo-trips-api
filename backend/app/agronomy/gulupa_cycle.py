"""
Modelo de desarrollo térmico y ciclo fenológico de Trips (Thripidae) en Gulupa (Passiflora edulis).
Cálculo de grados-día (Degree-Days) y predicción temporal según temperatura ambiental/invernadero.
"""

from typing import Dict, Any

# Constantes térmicas para Frankliniella occidentalis / Thrips tabaci
# Temperatura base mínima de desarrollo (T0)
T_BASE = 10.5  # °C

# Requerimientos térmicos aproximados en Grados-Día (GDD - Grados Día Acumulados)
THERMAL_REQUIREMENTS_GDD = {
    "huevo": 60.0,
    "larva": 95.0,   # Larva/Ninfa: único estadio larval (no se divide en I y II)
    "pupa": 55.0,
}
# Total ciclo huevo a emergencia de adulto: ~210 GDD

def calculate_stage_duration_days(gdd: float, temperature_c: float) -> float:
    """Calcula los días requeridos para un estadio dado el GDD y la temperatura efectiva."""
    effective_temp = max(temperature_c - T_BASE, 1.5)  # Evita división por cero o números negativos
    days = gdd / effective_temp
    # Limitar a rangos biológicos realistas
    return max(1.5, min(days, 35.0))

def get_gulupa_cycle_estimate(stage_key: str, temperature_c: float = 20.0) -> Dict[str, Any]:
    """
    Retorna la estimación del ciclo biológico, días restantes para alcanzar la fase adulta
    y el nivel de urgencia fitosanitaria en Gulupa según la temperatura actual.
    """
    temp = max(12.0, min(temperature_c, 34.0))  # Rango térmico normal de invernadero
    
    # Calcular duración de cada fase para la temperatura dada
    days_egg = calculate_stage_duration_days(THERMAL_REQUIREMENTS_GDD["huevo"], temp)
    days_larva = calculate_stage_duration_days(THERMAL_REQUIREMENTS_GDD["larva"], temp)
    days_pupa = calculate_stage_duration_days(THERMAL_REQUIREMENTS_GDD["pupa"], temp)
    
    stage_info = {
        "temperature_c": round(temp, 1),
        "detected_stage_key": stage_key,
        "detected_stage_name": "",
        "current_stage_duration_days": "",
        "days_to_adult": "",
        "urgency_level": "MODERADO",
        "urgency_rationale": ""
    }
    
    if stage_key == "adulto":
        stage_info.update({
            "detected_stage_name": "Adulto (Dispersión y Oviposición)",
            "current_stage_duration_days": f"Vive entre {round(200 / max(temp - 10, 4))} y {round(350 / max(temp - 10, 4))} días",
            "days_to_adult": "Estadio adulto activo (fase reproductora)",
            "urgency_level": "CRÍTICO",
            "urgency_rationale": (
                "Hembras adultas ovipositan hasta 200 huevos dentro de los tejidos de botones florales "
                "y hojas tiernas de Gulupa. Es la fase con mayor movilidad y capacidad de dispersar tospovirus. "
                "Requiere intervención inmediata con trampas azules y control etológico/químico selectivo."
            )
        })
    elif stage_key == "huevo":
        days_rem = round(days_larva + days_pupa, 1)
        stage_info.update({
            "detected_stage_name": "Huevo (Fase de Incubación)",
            "current_stage_duration_days": f"{round(days_egg, 1)} días a {temp}°C",
            "days_to_adult": f"{days_rem} días para alcanzar fase adulta tras la eclosión",
            "urgency_level": "ALTO",
            "urgency_rationale": (
                "Huevos insertados en los tejidos de botones florales y hojas tiernas. Aún no hay daño directo, "
                "pero la eclosión de larvas es inminente. Es el momento óptimo para reforzar el monitoreo de botones "
                "y la liberación preventiva de ácaros depredadores (Amblyseius swirskii) antes de que aparezcan las larvas."
            )
        })
    elif stage_key == "larva":
        days_rem = round(days_pupa, 1)
        stage_info.update({
            "detected_stage_name": "Larva / Ninfa (Fase de Raspado)",
            "current_stage_duration_days": f"{round(days_larva, 1)} días a {temp}°C",
            "days_to_adult": f"{days_rem} días (pasará a pupa y luego a adulto)",
            "urgency_level": "CRÍTICO",
            "urgency_rationale": (
                "La larva (ninfa) es el estadio con mayor consumo alimenticio. Si está presente en frutos recién "
                "cuajados (< 3 cm de diámetro), raspa la epidermis generando el 'cacarizado' o 'roña', "
                "provocando el rechazo total del fruto para exportación a Europa. Aplicar control foliar biológico o biorracional."
            )
        })
    elif stage_key == "pupa":
        days_rem = round(days_pupa * 0.6, 1)
        stage_info.update({
            "detected_stage_name": "Prepupa / Pupa (Fase Críptica en Reposo)",
            "current_stage_duration_days": f"{round(days_pupa, 1)} días a {temp}°C",
            "days_to_adult": f"{days_rem} días para emergencia masiva de adultos",
            "urgency_level": "ALTO",
            "urgency_rationale": (
                "Fase no alimentaria que suele refugiarse en grietas de las espalderas, corteza o capa superficial "
                "del suelo/sustrato. Indica que en pocos días emergerá una nueva cohorte de adultos. "
                "Considerar riego con nematodos entomopatógenos (Steinernema feltiae) o ácaros de suelo (Hypoaspis miles)."
            )
        })
    elif stage_key == "dano_gulupa":
        stage_info.update({
            "detected_stage_name": "Manifestación de Daño (Roña / Cacarizado en Fruto de Gulupa)",
            "current_stage_duration_days": "Lesión acumulativa irreversible en la epidermis del fruto",
            "days_to_adult": "Revisar envés foliar y botones para detectar ninfas o adultos activos",
            "urgency_level": "CRÍTICO",
            "urgency_rationale": (
                "La cicatriz corchosa ya visible confirma que el trips atacó durante la etapa tierna de cuaje floral. "
                "Se debe realizar monitoreo riguroso en los nuevos botones florales para cortar el ciclo de reproducción."
            )
        })
    else:
        stage_info.update({
            "detected_stage_name": "Monitoreo General de Trips",
            "current_stage_duration_days": f"Ciclo completo huevo-adulto: ~{round(days_egg + days_larva + days_pupa, 1)} días a {temp}°C",
            "days_to_adult": "Monitoreo preventivo",
            "urgency_level": "MODERADO",
            "urgency_rationale": "Mantener monitoreo continuo con trampas azules y revisar 20 botones florales por semana."
        })
        
    return stage_info
