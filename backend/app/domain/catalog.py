"""
Catálogo extensible de detección fitosanitaria.

Un *perfil* (profile) agrupa los objetivos (plagas, daño, sano, otros)
que se clasifican juntos y define sus estadios biológicos.

Para añadir una nueva plaga o enfermedad solo hay que registrar un
``DetectionTarget`` y un ``DetectionProfile`` en este archivo. El motor de ML,
la galería, la API y la interfaz web se adaptan automáticamente al catálogo.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Tipos de objetivo
# ---------------------------------------------------------------------------

KIND_PEST = "pest"
KIND_DISEASE = "disease"
KIND_DAMAGE = "damage"
KIND_HEALTHY = "healthy"
KIND_OTHER = "other"

VALID_KINDS = (KIND_PEST, KIND_DISEASE, KIND_DAMAGE, KIND_HEALTHY, KIND_OTHER)


@dataclass(frozen=True)
class DetectionTarget:
    """Una clase visual que el modelo puede reconocer (plaga, daño, sano...)."""

    key: str
    common_name: str
    kind: str
    prompts: Tuple[str, ...]
    scientific_name: Optional[str] = None
    description: str = ""

    def __post_init__(self) -> None:
        if self.kind not in VALID_KINDS:
            raise ValueError(f"Tipo de objetivo inválido '{self.kind}' para {self.key}")
        if not self.prompts:
            raise ValueError(f"El objetivo {self.key} debe tener al menos un prompt")


@dataclass(frozen=True)
class StageDefinition:
    """Estadio biológico de una plaga (huevo, larva, pupa, adulto o daño)."""

    key: str
    name: str
    description: str
    prompts: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.prompts:
            raise ValueError(f"El estadio {self.key} debe tener al menos un prompt")


@dataclass(frozen=True)
class DetectionProfile:
    """Conjunto de objetivos y estadios que se clasifican en una misma inferencia."""

    key: str
    name: str
    description: str
    target_keys: Tuple[str, ...]
    positive_target_keys: Tuple[str, ...]
    stages: Dict[str, StageDefinition]
    crop: Optional[str] = None
    min_confidence: float = 0.60
    min_margin: float = 0.05
    experimental: bool = False
    agronomy_provider: str = ""
    damage_stage_keys: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        missing = [k for k in self.target_keys if k not in TARGETS]
        if missing:
            raise ValueError(f"Perfil {self.key} referencia objetivos inexistentes: {missing}")
        missing_positive = [k for k in self.positive_target_keys if k not in self.target_keys]
        if missing_positive:
            raise ValueError(
                f"Perfil {self.key} tiene objetivos positivos fuera del perfil: {missing_positive}"
            )
        missing_damage = [k for k in self.damage_stage_keys if k not in self.stages]
        if missing_damage:
            raise ValueError(
                f"Perfil {self.key} tiene estadios de daño inexistentes: {missing_damage}"
            )

    def is_positive_target(self, target_key: str) -> bool:
        return target_key in self.positive_target_keys


@dataclass(frozen=True)
class GalleryLabel:
    """Carpeta de la galería de referencia y su significado dentro del catálogo."""

    key: str
    profile: str
    target: str
    stage: Optional[str]
    display_name: str

    @property
    def folder(self) -> str:
        return self.key


# ---------------------------------------------------------------------------
# Objetivos del perfil Trips (compatibilidad con la versión 1.x)
# ---------------------------------------------------------------------------

TARGETS: Dict[str, DetectionTarget] = {}


def _register(*targets: DetectionTarget) -> None:
    for target in targets:
        if target.key in TARGETS:
            raise ValueError(f"Objetivo duplicado en el catálogo: {target.key}")
        TARGETS[target.key] = target


_register(
    # --- Clases positivas: Trips -------------------------------------------------
    DetectionTarget(
        key="trips_frankliniella_occidentalis",
        common_name="Trips de las Flores",
        scientific_name="Frankliniella occidentalis",
        kind=KIND_PEST,
        description="Especie polífaga, principal vector de tospovirus en gulupa.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae Frankliniella occidentalis, "
            "western flower thrips on passionfruit leaf or flower",
            "A macro photograph of a western flower thrips, Frankliniella occidentalis, "
            "slender amber body with fringed wings on a green leaf",
        ),
    ),
    DetectionTarget(
        key="trips_frankliniella_panamensis",
        common_name="Trips de las Pasifloras",
        scientific_name="Frankliniella panamensis",
        kind=KIND_PEST,
        description="Presente con frecuencia en inflorescencias de pasifloráceas.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae Frankliniella, "
            "flower thrips insect on Passiflora edulis flower bud",
            "Close-up of a Frankliniella thrips resting on a purple passionflower, "
            "tiny elongated insect with fringed wings",
        ),
    ),
    DetectionTarget(
        key="trips_tabaci",
        common_name="Trips de la Cebolla",
        scientific_name="Thrips tabaci",
        kind=KIND_PEST,
        description="Especie polífaga de hojas tiernas y botones en épocas secas.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae Thrips tabaci, "
            "onion thrips slender elongated body on foliage",
            "Macro photo of an onion thrips, Thrips tabaci, pale yellow slender insect "
            "on a green plant leaf",
        ),
    ),
    DetectionTarget(
        key="trips_general",
        common_name="Trips",
        scientific_name="Thysanoptera: Thripidae",
        kind=KIND_PEST,
        description="Cualquier trips adulto o ninfa visible en la muestra.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae, "
            "close-up photo of a slender thrips insect pest",
            "Tiny elongated thrips insect with feathery fringed wings and segmented antennae "
            "on a plant leaf, macro photography",
        ),
    ),
    DetectionTarget(
        key="trips_dano_fruto_gulupa",
        common_name="Daño de Trips en Fruto de Gulupa",
        scientific_name=None,
        kind=KIND_DAMAGE,
        description="Roña o cacarizado corchoso causado por el raspado de ninfas.",
        prompts=(
            "Close-up photo of purple passionfruit (gulupa, Passiflora edulis) young green fruit "
            "showing severe thrips feeding damage, corky surface scarring, scab, cacarizado or roña",
            "Green passion fruit with silver-brown corky scars and rough epidermis caused by "
            "thrips feeding damage, agricultural plant disease symptom",
        ),
    ),
    # --- Clases negativas del perfil Trips --------------------------------------
    DetectionTarget(
        key="neg_mosca_blanca",
        common_name="Mosca Blanca",
        scientific_name="Bemisia tabaci",
        kind=KIND_PEST,
        description="Plaga confusora con trips; no es el objetivo del perfil Trips.",
        prompts=(
            "Animalia Arthropoda Insecta Hemiptera Aleyrodidae Bemisia tabaci, "
            "whitefly insect with powdery white wings on leaf underside",
            "Small whitefly with white waxy wings and pale body on the underside of a green leaf",
        ),
    ),
    DetectionTarget(
        key="neg_pulgon",
        common_name="Pulgón",
        scientific_name="Aphididae",
        kind=KIND_PEST,
        description="Insecto globular que se alimenta de savia.",
        prompts=(
            "Animalia Arthropoda Insecta Hemiptera Aphididae Aphis gossypii, "
            "globular soft-bodied aphid insect feeding on plant sap",
            "Cluster of small green pear-shaped aphids on a plant stem, macro photo",
        ),
    ),
    DetectionTarget(
        key="neg_arana_roja",
        common_name="Araña Roja",
        scientific_name="Tetranychus urticae",
        kind=KIND_PEST,
        description="Ácaro tetraníquido productor de telarañas finas.",
        prompts=(
            "Animalia Arthropoda Arachnida Trombidiformes Tetranychidae Tetranychus urticae, "
            "two-spotted spider mite tiny red or greenish mite with webbing",
            "Tiny red spider mites and fine silk webbing on the underside of a green leaf",
        ),
    ),
    DetectionTarget(
        key="neg_acaro_plano",
        common_name="Ácaro Plano",
        scientific_name="Brevipalpus",
        kind=KIND_PEST,
        description="Ácaro plano de las pasifloras.",
        prompts=(
            "Animalia Arthropoda Arachnida Trombidiformes Tenuipalpidae Brevipalpus, "
            "flat false spider mite on passionfruit vine",
            "Minute flat reddish mite attached to a green leaf surface, macro photograph",
        ),
    ),
    DetectionTarget(
        key="neg_mosca_minadora",
        common_name="Mosca Minadora",
        scientific_name="Liriomyza",
        kind=KIND_PEST,
        description="Larva que perfora galerías serpenteantes en la hoja.",
        prompts=(
            "Animalia Arthropoda Insecta Diptera Agromyzidae Liriomyza, "
            "leafminer serpentine white tunnels on passionfruit leaf",
            "Green leaf with winding white leaf miner tunnels and a small fly larva inside",
        ),
    ),
    DetectionTarget(
        key="neg_hoja_sana_gulupa",
        common_name="Hoja Sana de Gulupa",
        scientific_name="Passiflora edulis",
        kind=KIND_HEALTHY,
        description="Follaje sano sin insectos ni síntomas.",
        prompts=(
            "Plantae Tracheophyta Magnoliopsida Malpighiales Passifloraceae Passiflora edulis, "
            "close-up photo of green plant leaf, foliage background texture without any insects",
            "Healthy green passionfruit leaf with smooth surface and no pests or disease symptoms",
        ),
    ),
    DetectionTarget(
        key="neg_flor_sana_gulupa",
        common_name="Flor Sana de Gulupa",
        scientific_name="Passiflora edulis",
        kind=KIND_HEALTHY,
        description="Flor sana sin plagas ni daño.",
        prompts=(
            "Plantae Tracheophyta Magnoliopsida Malpighiales Passifloraceae Passiflora edulis, "
            "healthy fresh purple passionfruit flower with purple and white corona filaments without pests",
            "Passionflower in full bloom with purple and white filaments, clean and healthy",
        ),
    ),
    DetectionTarget(
        key="neg_zarcillo_tallo",
        common_name="Tallo o Zarcillo",
        scientific_name="Passiflora edulis",
        kind=KIND_OTHER,
        description="Estructura vegetal sin insectos.",
        prompts=(
            "Plantae Tracheophyta Magnoliopsida Passifloraceae Passiflora edulis, "
            "clean green plant stem, leaf petiole, vine background or climbing tendril",
            "Green passionfruit vine stem and curling tendril close-up, no insects",
        ),
    ),
    DetectionTarget(
        key="neg_mancha_polvo_caldo",
        common_name="Polvo, Caldo o Gota Seca",
        scientific_name=None,
        kind=KIND_OTHER,
        description="Artefacto visual que puede confundirse con una lesión.",
        prompts=(
            "Dried water drop, agricultural pesticide powder residue or soil dust dirt speck on leaf surface",
            "White dried spray residue or dust spots on a green leaf, not a plant disease",
        ),
    ),
)

# Alias retrocompatible: los nombres antiguos "neg_*" siguen existiendo.
TRIPS_TARGET_KEYS: Tuple[str, ...] = tuple(TARGETS.keys())


# ---------------------------------------------------------------------------
# Estadios del perfil Trips
# ---------------------------------------------------------------------------

TRIPS_STAGES: Dict[str, StageDefinition] = {
    "huevo": StageDefinition(
        key="huevo",
        name="Huevo",
        description="Huevo ovalado, translúcido o blanquecino, insertado en el tejido vegetal",
        prompts=(
            "A high-magnification macro photo of a thrips egg, oval translucent whitish egg "
            "inserted inside plant tissue, leaf epidermis, flower bud or young fruit surface "
            "of passionfruit (Passiflora edulis), tiny smooth egg without legs or wings.",
        ),
    ),
    "larva": StageDefinition(
        key="larva",
        name="Larva (Ninfa)",
        description="Estadio larval o ninfal, sin alas, translúcido a amarillo/anaranjado, activo",
        prompts=(
            "A close-up macro photo of a thrips larva, also called nymph, wingless elongated "
            "soft body of translucent white, pale yellow or light orange color, tiny legs, "
            "actively walking and rasping plant tissue or young green fruit surface.",
        ),
    ),
    "pupa": StageDefinition(
        key="pupa",
        name="Pupa (Prepupa)",
        description="Estadio en reposo (pseudopupa), inmóvil con esbozos alares visibles",
        prompts=(
            "A close-up photo of a thrips prepupa or pupa, inactive non-feeding stage, "
            "pale body with short wing buds or pads visible along thorax and abdomen, "
            "resting in a crevice, leaf litter or soil.",
        ),
    ),
    "adulto": StageDefinition(
        key="adulto",
        name="Adulto",
        description="Adulto móvil con alas franjeadas y cuerpo alargado pardo o amarillento",
        prompts=(
            "A macroscopic photo of an adult thrips insect (Frankliniella occidentalis or Thrips tabaci), "
            "elongated slender dark amber or brown body with long narrow fringed feathered wings "
            "and visible segmented antennae resting on plant leaf or flower petal.",
        ),
    ),
    "dano_gulupa": StageDefinition(
        key="dano_gulupa",
        name="Daño Fitosanitario (Roña / Cacarizado en Fruto o Flor)",
        description="Lesión corchosa plateada/parda en fruto verde de Gulupa o deformación de botón",
        prompts=(
            "Severe thrips feeding damage symptoms on purple passionfruit (gulupa, Passiflora edulis): "
            "corky scab, silvering spots, rough brown scarring (cacarizado, roña) on young green fruit epidermis, "
            "chlorotic stippling and black fecal specks on foliage.",
        ),
    ),
}


# ---------------------------------------------------------------------------
# Objetivos del perfil Moscas
# ---------------------------------------------------------------------------

_register(
    DetectionTarget(
        key="mosca_blanca_bemisia",
        common_name="Mosca Blanca",
        scientific_name="Bemisia tabaci",
        kind=KIND_PEST,
        description="Mosca blanca con alas cerosas; clase confusora del perfil Moscas de la Fruta.",
        prompts=(
            "Animalia Arthropoda Insecta Hemiptera Aleyrodidae Bemisia tabaci, "
            "adult whitefly with powdery white wings on the underside of a green leaf",
            "Macro photo of a whitefly adult, Bemisia tabaci, pale body and white waxy wings "
            "resting on a passionfruit leaf",
            "Whitefly eggs and nymphs on the underside of a leaf, tiny oval pale scales",
        ),
    ),
    DetectionTarget(
        key="mosca_frutal_anastrepha",
        common_name="Mosca de la Fruta",
        scientific_name="Anastrepha spp.",
        kind=KIND_PEST,
        description="Mosca de la fruta que oviposita en frutos y causa pérdidas de exportación.",
        prompts=(
            "Animalia Arthropoda Insecta Diptera Tephritidae Anastrepha, "
            "fruit fly with patterned wings on a passionfruit",
            "Macro photo of a yellow-brown fruit fly, Anastrepha, with banded wings and long ovipositor",
            "Fruit fly larva inside a damaged passionfruit, white maggot in fruit pulp",
        ),
    ),
    DetectionTarget(
        key="mosca_minadora_liriomyza",
        common_name="Mosca Minadora",
        scientific_name="Liriomyza spp.",
        kind=KIND_PEST,
        description="Pequeña mosca minadora; clase confusora del perfil Moscas de la Fruta.",
        prompts=(
            "Animalia Arthropoda Insecta Diptera Agromyzidae Liriomyza, "
            "small leafminer fly on a passionfruit leaf",
            "Serpentine leaf mine tunnels with a small white fly larva inside a green leaf",
            "Macro photograph of a tiny black and yellow leafminer fly resting on foliage",
        ),
    ),
    DetectionTarget(
        key="mosca_neg_trips",
        common_name="Trips",
        scientific_name="Thysanoptera: Thripidae",
        kind=KIND_PEST,
        description="Trips; no es el objetivo del perfil Moscas.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae, "
            "slender thrips insect with fringed wings on a plant",
        ),
    ),
    DetectionTarget(
        key="mosca_neg_pulgon",
        common_name="Pulgón",
        scientific_name="Aphididae",
        kind=KIND_PEST,
        description="Pulgón; no es el objetivo del perfil Moscas.",
        prompts=(
            "Animalia Arthropoda Insecta Hemiptera Aphididae, "
            "small globular aphid insects clustered on a plant stem",
        ),
    ),
    DetectionTarget(
        key="mosca_neg_arana_roja",
        common_name="Araña Roja",
        scientific_name="Tetranychus urticae",
        kind=KIND_PEST,
        description="Araña roja; no es el objetivo del perfil Moscas.",
        prompts=(
            "Animalia Arthropoda Arachnida Trombidiformes Tetranychidae Tetranychus urticae, "
            "tiny red spider mite with fine webbing on a leaf",
        ),
    ),
    DetectionTarget(
        key="mosca_neg_hoja_sana",
        common_name="Hoja Sana",
        scientific_name="Passiflora edulis",
        kind=KIND_HEALTHY,
        description="Follaje sano sin moscas.",
        prompts=(
            "Healthy green passionfruit leaf with no insects, no mines and no disease symptoms",
        ),
    ),
    DetectionTarget(
        key="mosca_neg_dano_mecanico",
        common_name="Daño Mecánico o Polvo",
        scientific_name=None,
        kind=KIND_OTHER,
        description="Artefacto visual sin relación con moscas.",
        prompts=(
            "Mechanical tear, dust spot or dried water residue on a green leaf surface",
        ),
    ),
)

MOSCAS_STAGES: Dict[str, StageDefinition] = {
    "huevo": StageDefinition(
        key="huevo",
        name="Huevo",
        description="Huevo alargado insertado bajo la epidermis del fruto",
        prompts=(
            "Macro photo of an elongated white fruit fly egg inserted under the skin of a "
            "passionfruit, oviposition puncture visible",
        ),
    ),
    "larva": StageDefinition(
        key="larva",
        name="Larva (Maggot)",
        description="Larva blanca apoda que se alimenta de la pulpa del fruto",
        prompts=(
            "Macro photo of a white legless fruit fly maggot inside the pulp of a damaged "
            "passionfruit, Anastrepha larva",
        ),
    ),
    "pupa": StageDefinition(
        key="pupa",
        name="Pupa (Pupario)",
        description="Pupario parduzco en el suelo o en frutos caídos",
        prompts=(
            "Close-up of a brown oval fruit fly puparium resting in soil or inside a fallen "
            "passionfruit",
        ),
    ),
    "adulto": StageDefinition(
        key="adulto",
        name="Adulto",
        description="Mosca de la fruta con alas bandeadas y ovipositor visible",
        prompts=(
            "Macro photo of an adult fruit fly, Anastrepha, yellow-brown body with patterned "
            "banded wings and pointed ovipositor resting on a passionfruit",
        ),
    ),
    "dano": StageDefinition(
        key="dano",
        name="Daño por Mosca de la Fruta",
        description="Picadura de oviposición, pudrición y larvas en el fruto",
        prompts=(
            "Fruit fly damage on a passionfruit: brown oviposition puncture, soft rotting "
            "area and white maggots inside the fruit",
        ),
    ),
}


# ---------------------------------------------------------------------------
# Objetivos del perfil Arañas Rojas
# ---------------------------------------------------------------------------

_register(
    DetectionTarget(
        key="arana_roja_tetranychus",
        common_name="Araña Roja",
        scientific_name="Tetranychus urticae",
        kind=KIND_PEST,
        description=(
            "Ácaro tetraníquido que produce punteado clorótico y telaraña fina en el envés."
        ),
        prompts=(
            "Animalia Arthropoda Arachnida Trombidiformes Tetranychidae Tetranychus urticae, "
            "two-spotted spider mite tiny red or greenish mite with fine silk webbing on a leaf",
            "Macro photograph of red spider mites clustered on the underside of a passionfruit leaf, "
            "fine web threads and yellow stippling damage",
            "Tiny reddish eight-legged spider mites and eggs on a green leaf surface, high magnification",
        ),
    ),
    DetectionTarget(
        key="arana_neg_trips",
        common_name="Trips",
        scientific_name="Thysanoptera: Thripidae",
        kind=KIND_PEST,
        description="Trips; no es el objetivo del perfil Arañas Rojas.",
        prompts=(
            "Animalia Arthropoda Insecta Thysanoptera Thripidae, "
            "slender thrips insect with fringed wings on a plant leaf",
        ),
    ),
)

ARANAS_ROJAS_STAGES: Dict[str, StageDefinition] = {
    "huevo": StageDefinition(
        key="huevo",
        name="Huevo",
        description="Huevos esféricos y translúcidos agrupados junto a la nervadura",
        prompts=(
            "Macro photo of tiny spherical translucent red spider mite eggs grouped on the "
            "underside of a green leaf near the veins",
        ),
    ),
    "larva": StageDefinition(
        key="larva",
        name="Ninfa (Larva)",
        description="Ninfa móvil de seis u ocho patas, más pequeña que el adulto",
        prompts=(
            "Macro photo of a red spider mite nymph, tiny six-legged or eight-legged pale "
            "reddish mite walking on a leaf surface",
        ),
    ),
    "adulto": StageDefinition(
        key="adulto",
        name="Adulto",
        description="Adulto de ocho patas, rojo o verdoso, con dos manchas oscuras",
        prompts=(
            "Macro photo of an adult two-spotted spider mite, Tetranychus urticae, "
            "eight-legged reddish or greenish mite with two dark spots on a leaf",
        ),
    ),
    "dano": StageDefinition(
        key="dano",
        name="Daño por Araña Roja (Telaraña / Punteado)",
        description="Punteado clorótico, bronceado y telaraña fina en el envés",
        prompts=(
            "Red spider mite feeding damage on a green leaf: yellow chlorotic stippling, "
            "bronzing and fine silk webbing on the leaf underside",
        ),
    ),
}


# ---------------------------------------------------------------------------
# Perfiles de detección
# ---------------------------------------------------------------------------

TRIPS_PROFILE = DetectionProfile(
    key="trips",
    name="Trips",
    description="Detección de trips, sus estadios biológicos y el daño en gulupa.",
    crop="gulupa",
    target_keys=tuple(
        key for key in TARGETS.keys() if key.startswith(("trips_", "neg_"))
    ),
    positive_target_keys=(
        "trips_frankliniella_occidentalis",
        "trips_frankliniella_panamensis",
        "trips_tabaci",
        "trips_general",
        "trips_dano_fruto_gulupa",
    ),
    stages=TRIPS_STAGES,
    min_confidence=0.60,
    min_margin=0.05,
    agronomy_provider="gulupa_trips",
    damage_stage_keys=("dano_gulupa",),
)

MOSCAS_PROFILE = DetectionProfile(
    key="moscas",
    name="Moscas de la Fruta",
    description=(
        "Detección de moscas de la fruta (Anastrepha) y su daño en frutos de gulupa. "
        "Las moscas blancas y minadoras se usan solo como clases confusoras."
    ),
    crop="gulupa",
    target_keys=tuple(
        key for key in TARGETS.keys() if key.startswith(("mosca_",))
    ),
    positive_target_keys=("mosca_frutal_anastrepha",),
    stages=MOSCAS_STAGES,
    min_confidence=0.60,
    min_margin=0.05,
    experimental=False,
    agronomy_provider="fruit_flies",
    damage_stage_keys=("dano",),
)

ARANAS_ROJAS_PROFILE = DetectionProfile(
    key="aranas_rojas",
    name="Arañas Rojas",
    description=(
        "Detección de araña roja (Tetranychus urticae), sus estadios y el daño "
        "por punteado y telaraña en gulupa."
    ),
    crop="gulupa",
    target_keys=(
        "arana_roja_tetranychus",
        "arana_neg_trips",
        "neg_mosca_blanca",
        "neg_pulgon",
        "neg_acaro_plano",
        "neg_hoja_sana_gulupa",
        "neg_flor_sana_gulupa",
        "neg_zarcillo_tallo",
        "neg_mancha_polvo_caldo",
    ),
    positive_target_keys=("arana_roja_tetranychus",),
    stages=ARANAS_ROJAS_STAGES,
    min_confidence=0.60,
    min_margin=0.05,
    experimental=False,
    agronomy_provider="red_spider_mites",
    damage_stage_keys=("dano",),
)

# ---------------------------------------------------------------------------
# Perfil universal / auto-detección (Cualquier plaga o tejido sano)
# ---------------------------------------------------------------------------

AUTO_TARGET_KEYS: Tuple[str, ...] = (
    # Trips
    "trips_frankliniella_occidentalis",
    "trips_frankliniella_panamensis",
    "trips_tabaci",
    "trips_general",
    "trips_dano_fruto_gulupa",
    # Moscas
    "mosca_frutal_anastrepha",
    # Arañas
    "arana_roja_tetranychus",
    # Otras plagas comunes en Gulupa
    "neg_mosca_blanca",
    "neg_pulgon",
    "neg_acaro_plano",
    "neg_mosca_minadora",
    # Tejido vegetal sano / otros
    "neg_hoja_sana_gulupa",
    "neg_flor_sana_gulupa",
    "neg_zarcillo_tallo",
    "neg_mancha_polvo_caldo",
)

AUTO_POSITIVE_TARGET_KEYS: Tuple[str, ...] = (
    "trips_frankliniella_occidentalis",
    "trips_frankliniella_panamensis",
    "trips_tabaci",
    "trips_general",
    "trips_dano_fruto_gulupa",
    "mosca_frutal_anastrepha",
    "arana_roja_tetranychus",
    "neg_mosca_blanca",
    "neg_pulgon",
    "neg_acaro_plano",
    "neg_mosca_minadora",
)

AUTO_PROFILE = DetectionProfile(
    key="auto",
    name="Auto-Detección (Cualquier Plaga)",
    description=(
        "Detecta automáticamente cualquier insecto plaga, ácaro o síntoma fitosanitario "
        "(Trips, Moscas de la fruta, Arañas rojas, Mosca blanca, Pulgón, Ácaro plano) o tejido sano."
    ),
    target_keys=AUTO_TARGET_KEYS,
    positive_target_keys=AUTO_POSITIVE_TARGET_KEYS,
    stages=TRIPS_STAGES,
    crop="gulupa",
    min_confidence=0.50,
    min_margin=0.02,
    experimental=False,
    agronomy_provider="auto",
    damage_stage_keys=("dano_gulupa",),
)

PROFILES: Dict[str, DetectionProfile] = {
    profile.key: profile
    for profile in (AUTO_PROFILE, TRIPS_PROFILE, MOSCAS_PROFILE, ARANAS_ROJAS_PROFILE)
}

DEFAULT_PROFILE_KEY = "auto"


def get_profile(profile_key: Optional[str]) -> DetectionProfile:
    """Devuelve el perfil solicitado o el perfil por defecto."""

    key = (profile_key or DEFAULT_PROFILE_KEY).strip().lower()
    try:
        return PROFILES[key]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILES))
        raise KeyError(f"Perfil de detección no válido '{profile_key}'. Válidos: {valid}") from exc


def get_target(target_key: str) -> DetectionTarget:
    try:
        return TARGETS[target_key]
    except KeyError as exc:
        raise KeyError(f"Objetivo no registrado en el catálogo: {target_key}") from exc


def list_profiles() -> List[DetectionProfile]:
    return list(PROFILES.values())


# ---------------------------------------------------------------------------
# Galería de referencia
# ---------------------------------------------------------------------------

LEGACY_TRIPS_LABEL_KEYS = tuple(TRIPS_STAGES.keys())


def _build_gallery_labels() -> Dict[str, GalleryLabel]:
    labels: Dict[str, GalleryLabel] = {}

    # Las carpetas históricas de trips se conservan en la raíz de la galería:
    # data/reference_gallery/huevo, .../larva, .../pupa, .../adulto, .../dano_gulupa
    for stage_key, stage in TRIPS_STAGES.items():
        labels[stage_key] = GalleryLabel(
            key=stage_key,
            profile="trips",
            target="trips_general",
            stage=stage_key,
            display_name=f"Trips · {stage.name}",
        )

    # Los perfiles nuevos usan una carpeta por perfil/objetivo/estadio.
    for profile in PROFILES.values():
        if profile.key == DEFAULT_PROFILE_KEY:
            continue
        for target_key in profile.positive_target_keys:
            target = get_target(target_key)
            for stage_key, stage in profile.stages.items():
                label_key = f"{profile.key}/{target_key}/{stage_key}"
                labels[label_key] = GalleryLabel(
                    key=label_key,
                    profile=profile.key,
                    target=target_key,
                    stage=stage_key,
                    display_name=f"{profile.name} · {target.common_name} · {stage.name}",
                )

    return labels


GALLERY_LABELS: Dict[str, GalleryLabel] = _build_gallery_labels()


def build_gallery_label_key(profile_key: str, target_key: str, stage_key: Optional[str]) -> str:
    """Construye la clave de carpeta de galería para un perfil/objetivo/estadio."""

    profile = get_profile(profile_key)
    if profile.key == DEFAULT_PROFILE_KEY and target_key == "trips_general" and stage_key in TRIPS_STAGES:
        return stage_key
    if profile.key == DEFAULT_PROFILE_KEY and stage_key in TRIPS_STAGES:
        return stage_key
    parts = [profile.key, target_key]
    if stage_key:
        parts.append(stage_key)
    return "/".join(parts)


def get_gallery_label(label_key: str) -> GalleryLabel:
    try:
        return GALLERY_LABELS[label_key]
    except KeyError as exc:
        valid = ", ".join(sorted(GALLERY_LABELS))
        raise KeyError(f"Carpeta de galería no válida '{label_key}'. Válidas: {valid}") from exc


def list_gallery_labels(profile_key: Optional[str] = None) -> List[GalleryLabel]:
    labels = list(GALLERY_LABELS.values())
    if profile_key:
        profile = get_profile(profile_key)
        labels = [label for label in labels if label.profile == profile.key]
    return labels
