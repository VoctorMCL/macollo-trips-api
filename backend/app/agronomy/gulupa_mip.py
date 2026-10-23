"""
Recomendaciones de Manejo Integrado de Plagas (MIP) especializadas para Trips
en el cultivo de Gulupa (Passiflora edulis f. edulis).
Enfoque en calidad de fruta de exportación, prevención de cacarizado/roña y rotación IRAC.
"""

from typing import Dict, Any, List

def get_gulupa_mip_recommendations(stage_key: str, is_damage_only: bool = False) -> Dict[str, Any]:
    """Genera recomendaciones fitosanitarias estructuradas para Gulupa según el estadio detectado."""
    
    # 1. Control Biológico
    bio_control: List[str] = [
        "Liberación de ácaros depredadores benéficos: Amblyseius swirskii o Neoseiulus cucumeris (dosis preventiva: 1-2 ind/m²; dosis curativa: 5-10 ind/m² en focos). Consumen vorazmente las larvas (ninfas) y los huevos de trips.",
        "Introducción de chinches piratas Orius insidiosus u Orius laevigatus (0.5 a 1 ind/m² en floración). Son los depredadores naturales más efectivos de trips adultos y ninfas dentro de las flores de Gulupa.",
        "Aplicación de hongo entomopatógeno Beauveria bassiana (cepa comercial a dosis de 1.5 - 2.0 g/L o ml/L) o Lecanicillium lecanii al atardecer (>60% HR, evitando degradación por radiación UV solar)."
    ]
    if stage_key == "huevo":
        bio_control.append(
            "Reforzar la liberación preventiva de Amblyseius swirskii y Orius spp. sobre botones florales: "
            "los huevos de trips están insertados en el tejido y la eclosión larval ocurre en pocos días, "
            "por lo que el control debe instalarse antes de que aparezca el daño."
        )
    if stage_key == "pupa":
        bio_control.append(
            "Aplicación al suelo/sustrato en el plateo de la planta de nematodos entomopatógenos Steinernema feltiae "
            "(250.000 a 500.000 JI/m²) o ácaros de suelo Stratiolaelaps scimitus (Hypoaspis miles) para controlar prepupas y pupas en reposo."
        )

    # 2. Control Etológico y Monitoreo
    ethological_control: List[str] = [
        "Instalación de trampas cromotrópicas adhesivas AZULES (longitud de onda reflectante ~460 nm). Es el color de máxima atracción para Frankliniella occidentalis.",
        "Ubicación de trampas: Colocar en el sistema de tutorado/espaldera a la altura del estrato productivo (brotes tiernos y botones florales).",
        "Densidad recomendada: 1 trampa cada 20 m² para monitoreo continuo; 1 trampa cada 8-10 m² en bordes y focos de invernadero para trampeo masivo.",
        "Monitoreo semanal: Sacudir 20 flores y 20 brotes tiernos sobre una superficie blanca para conteo directo. Umbral de acción: > 1-2 trips/flor en época de cuaje."
    ]

    # 3. Control Cultural
    cultural_control: List[str] = [
        "Poda sanitaria y aclareo de zarcillos secos y hojas senescentes en la espaldera para mejorar ventilación y penetración de aspersiones fitosanitarias.",
        "Erradicación estricta de malezas reservorio hospederas en calles y perímetro del lote (Cerraja: Sonchus oleraceus; Chipaca: Bidens pilosa; Malva spp.).",
        "Manejo de humedad relativa: Mantener la HR entre 65% y 75% en el invernadero mediante nebulización o ventilación. Ambientes secos (HR < 50%) aceleran exponencialmente la reproducción de trips.",
        "Mallas anti-insectos (mínimo 50 mesh / 10x20 hilos por cm²) en ventanas laterales y cenitales del invernadero con doble puerta de acceso."
    ]

    # 4. Control Biorracional y Químico (con rotación estricta de modo de acción IRAC)
    chemical_biorational: List[str] = [
        "Biorracional de contacto: Jabón potásico (3-5 cc/L) en mezcla con extracto de Neem (Azadiractina 1%, 1.5 cc/L). Bloquea la muda de ninfas y actúa como repelente anti-alimentario.",
        "Aceites esenciales agrícolas: Extracto de canela o aceite de naranja para degradar la cutícula del insecto y deshidratarlo sin generar resistencia.",
        "Grupo IRAC 5 (Espinocinas): Spinosad (0.2 - 0.4 cc/L) o Spinetoram. Excelente eficacia por ingestión y contacto en adultos y ninfas. Usar máximo 2 aplicaciones seguidas por ciclo.",
        "Grupo IRAC 29 (Bloqueadores de alimentación): Flonicamid (0.15 - 0.2 g/L). Detiene la alimentación por estilete en menos de 1 hora, preservando fauna benéfica.",
        "Grupo IRAC 6 (Avermectinas): Abamectina (0.5 - 0.75 cc/L) en mezcla con aceite mineral parafínico coadyuvante (0.25%).",
        "ADVERTENCIA DE ROTACIÓN: Los trips desarrollan resistencia a insecticidas con extrema rapidez. Es obligatorio rotar entre diferentes grupos IRAC (ej. IRAC 5 -> IRAC 29 -> IRAC 6) en cada ventana de aplicación."
    ]

    # 5. Alerta específica de impacto económico en Gulupa para Exportación
    export_alert = (
        "ALERTA GULUPA EXPORTACIÓN: El raspado de trips en flores recién fecundadas y frutitos en cuaje "
        "(menores a 3 cm) induce cicatrización hipertrófica peridérmica ('roña' o 'cacarizado'). "
        "Frutos con más de 1 cm² de lesión son descartados automáticamente de cajas de exportación tipo Europa (GlobalG.A.P.). "
        "Intervenir preventivamente en pre-floración y caída de pétalos."
    )

    return {
        "biological_control": bio_control,
        "ethological_control": ethological_control,
        "cultural_control": cultural_control,
        "chemical_biorational_control": chemical_biorational,
        "export_impact_alert": export_alert
    }
