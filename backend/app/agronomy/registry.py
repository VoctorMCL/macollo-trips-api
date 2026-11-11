"""Registro de proveedores agronómicos por perfil de detección."""

from typing import Any, Dict, Optional, Tuple

from backend.app.agronomy.flies import (
    get_fly_cycle_estimate,
    get_fly_mip_recommendations,
)
from backend.app.agronomy.gulupa_cycle import get_gulupa_cycle_estimate
from backend.app.agronomy.gulupa_mip import get_gulupa_mip_recommendations
from backend.app.agronomy.mites import (
    get_mite_cycle_estimate,
    get_mite_mip_recommendations,
)

COMMON_PESTS_MIP: Dict[str, Dict[str, Any]] = {
    "mosca_blanca": {
        "target_name": "Mosca Blanca (Bemisia tabaci)",
        "biological_control": [
            "Liberación de parasitoides Encarsia formosa o depredadores Chrysoperla carnea.",
            "Aplicación foliar de hongos entomopatógenos (Beauveria bassiana, Lecanicillium lecanii)."
        ],
        "ethological_control": [
            "Instalación de trampas adhesivas cromáticas amarillas a la altura del dosel vegetal.",
            "Monitoreo semanal del envés de hojas tiernas."
        ],
        "cultural_control": [
            "Eliminación y quema/entierro de arvenses hospederas en bordes de lote.",
            "Evitar siembras escalonadas contiguas sin periodo de descanso."
        ],
        "chemical_biorational": [
            "Aplicación focalizada de jabón potásico (1-2%) o sales potásicas de ácidos grasos.",
            "Extracto concentrado de neem (azadiractina) en etapas de ninfa temprana."
        ],
        "irac_mode_of_action": "Rotación estricta: Grupo 7C (Piriproxifeno) con Grupo 23 (Spiromesifen) para evitar resistencia.",
        "export_impact_alert": "Controlar colonias antes de floración para evitar fumagina sobre frutos de exportación."
    },
    "pulgon": {
        "target_name": "Pulgones (Aphididae: Aphis gossypii)",
        "biological_control": [
            "Conservación y liberación de mariquitas (Coccinellidae) y larvas de crisopa (Chrysoperla).",
            "Protección de avispitas parasitoides nativas (Aphidius colemani)."
        ],
        "ethological_control": [
            "Trampas cromáticas amarillas en cabeceras de surco para detección temprana de formas aladas.",
            "Inspección de brotes tiernos en busca de hojas enrolladas."
        ],
        "cultural_control": [
            "Poda y retiro de brotes tiernos con colonias densas y presencia de mielecilla.",
            "Control de hormigas en la base de la planta (evitan que defiendan a los pulgones)."
        ],
        "chemical_biorational": [
            "Aplicación de extracto de ajo-ají o jabón agrícola para disolver la cutícula del insecto.",
            "En alta presión: Flonicamid o Pimetrozina aplicados dirigidos al cogollo."
        ],
        "irac_mode_of_action": "Rotación IRAC: Grupo 29 (bloqueadores cordotonales) con Grupo 4D (Butenolidas).",
        "export_impact_alert": "Pulgones transmiten virosis graves en pasifloráceas (PWV). Actuar al primer foco."
    },
    "acaro_plano": {
        "target_name": "Ácaro Plano de las Pasifloras (Brevipalpus spp.)",
        "biological_control": [
            "Fomento de ácaros depredadores nativos de la familia Phytoseiidae (Neoseiulus, Amblyseius).",
            "Aplicación de acaricidas microbiológicos como Hirsutella thompsonii."
        ],
        "ethological_control": [
            "Monitoreo con lupa 20x-40x en el envés foliar y corteza de tallos lignificados.",
            "Marcar focos con cintas para seguimiento quincenal."
        ],
        "cultural_control": [
            "Manejo de podas de ventilación para evitar microclimas estancados y secos.",
            "Riego oportuno para evitar estrés hídrico que favorece la dispersión del ácaro."
        ],
        "chemical_biorational": [
            "Azufre elemental en formulación líquida micronizada (no mezclar con aceites minerales).",
            "Aceites vegetales emulsificados en horas tempranas de la mañana."
        ],
        "irac_mode_of_action": "Rotación IRAC: Grupo 10B (Etoxazol) alternado con Grupo 21A (Fenpiroximato / Tebufenpirad).",
        "export_impact_alert": "Vector del virus de la mancha verde de la gulupa. Cero tolerancia en plantas madre."
    },
    "mosca_minadora": {
        "target_name": "Mosca Minadora (Liriomyza spp.)",
        "biological_control": [
            "Protección de microavispas parasitoides de larvas (Diglyphus isaea, Dacnusa sibirica).",
            "Aplicación de nematodos entomopatógenos (Steinernema feltiae)."
        ],
        "ethological_control": [
            "Trampas adhesivas amarillas situadas a 30 cm por encima del follaje para captura de adultos.",
            "Conteo de minas activas por hoja."
        ],
        "cultural_control": [
            "Recolección manual y destrucción de hojas bajeras con galerías activas con larva viva.",
            "Destrucción de rastrojos de cosecha inmediatamente después del ciclo."
        ],
        "chemical_biorational": [
            "Azadiractina foliar (inhibe la muda de larvas dentro de la galería).",
            "Ciromazina (regulador de crecimiento específico para larvas de dípteros)."
        ],
        "irac_mode_of_action": "Rotación IRAC: Grupo 17 (reguladores de muda) con Grupo 5 (Spinosinas).",
        "export_impact_alert": "Afecta el área fotosintética foliar y puede descalificar hojas de acompañamiento."
    }
}


def get_agronomy(
    profile_key: str,
    stage_key: str,
    temperature_c: float,
    target_key: Optional[str] = None,
    is_damage_only: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Devuelve ``(cycle_info, recommendations)`` para el perfil o plaga solicitada."""

    if profile_key in ("trips", "auto") and (not target_key or target_key.startswith("trips")):
        cycle = get_gulupa_cycle_estimate(stage_key, temperature_c)
        recommendations = get_gulupa_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        cycle.setdefault("profile", "trips")
        return cycle, recommendations

    if profile_key == "moscas" or (target_key and target_key.startswith("mosca_frutal")):
        cycle = get_fly_cycle_estimate(stage_key, temperature_c)
        recommendations = get_fly_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        return cycle, recommendations

    if profile_key == "aranas_rojas" or (target_key and target_key.startswith("arana_roja")):
        cycle = get_mite_cycle_estimate(stage_key, temperature_c)
        recommendations = get_mite_mip_recommendations(
            stage_key, is_damage_only=is_damage_only
        )
        return cycle, recommendations

    # Recomendaciones específicas para otras plagas del catálogo
    clean_target = (target_key or "").replace("neg_", "").replace("_bemisia", "").replace("_liriomyza", "")
    for pest_key, mip_data in COMMON_PESTS_MIP.items():
        if pest_key in clean_target:
            return None, mip_data

    return None, None
