"""
Definición de jerarquías taxonómicas, descripciones biológicas y prompts para BioCLIP 2.5
enfocados exclusivamente en Trips (Thysanoptera: Thripidae) y el cultivo de Gulupa (Passiflora edulis).
"""

from typing import Dict, List

# 1. Prompts de clasificación binaria / multiclase de objetivo
# Permite a BioCLIP discriminar si la imagen es un Trips o un organismo/objeto confusor en Gulupa.
TAXONOMIC_TARGET_PROMPTS = {
    # Clase Positiva: Trips (Thysanoptera: Thripidae)
    "trips_frankliniella_occidentalis": (
        "Animalia Arthropoda Insecta Thysanoptera Thripidae Frankliniella occidentalis, "
        "western flower thrips on passionfruit leaf or flower"
    ),
    "trips_frankliniella_panamensis": (
        "Animalia Arthropoda Insecta Thysanoptera Thripidae Frankliniella, "
        "flower thrips insect on Passiflora edulis flower bud"
    ),
    "trips_tabaci": (
        "Animalia Arthropoda Insecta Thysanoptera Thripidae Thrips tabaci, "
        "onion thrips slender elongated body on foliage"
    ),
    "trips_general": (
        "Animalia Arthropoda Insecta Thysanoptera Thripidae, "
        "close-up photo of a slender thrips insect pest"
    ),
    "trips_dano_fruto_gulupa": (
        "Close-up photo of purple passionfruit (gulupa, Passiflora edulis) young green fruit "
        "showing severe thrips feeding damage, corky surface scarring, scab, cacarizado or roña"
    ),

    # Clases Negativas: Plagas confusoras y fauna común en invernaderos de pasifloras
    "neg_mosca_blanca": (
        "Animalia Arthropoda Insecta Hemiptera Aleyrodidae Bemisia tabaci, "
        "whitefly insect with powdery white wings on leaf underside"
    ),
    "neg_pulgon": (
        "Animalia Arthropoda Insecta Hemiptera Aphididae Aphis gossypii, "
        "globular soft-bodied aphid insect feeding on plant sap"
    ),
    "neg_arana_roja": (
        "Animalia Arthropoda Arachnida Trombidiformes Tetranychidae Tetranychus urticae, "
        "two-spotted spider mite tiny red or greenish mite with webbing"
    ),
    "neg_acaro_plano": (
        "Animalia Arthropoda Arachnida Trombidiformes Tenuipalpidae Brevipalpus, "
        "flat false spider mite on passionfruit vine"
    ),
    "neg_mosca_minadora": (
        "Animalia Arthropoda Insecta Diptera Agromyzidae Liriomyza, "
        "leafminer serpentine white tunnels on passionfruit leaf"
    ),

    # Clases Negativas: Estructuras vegetales sanas y artefactos visuales
    "neg_hoja_sana_gulupa": (
        "Plantae Tracheophyta Magnoliopsida Malpighiales Passifloraceae Passiflora edulis, "
        "close-up photo of green plant leaf, foliage background texture without any insects"
    ),
    "neg_flor_sana_gulupa": (
        "Plantae Tracheophyta Magnoliopsida Malpighiales Passifloraceae Passiflora edulis, "
        "healthy fresh purple passionfruit flower with purple and white corona filaments without pests"
    ),
    "neg_zarcillo_tallo": (
        "Plantae Tracheophyta Magnoliopsida Passifloraceae Passiflora edulis, "
        "clean green plant stem, leaf petiole, vine background or climbing tendril"
    ),
    "neg_mancha_polvo_caldo": (
        "Dried water drop, agricultural pesticide powder residue or soil dust dirt speck on leaf surface"
    )
}

# 2. Prompts de clasificación de estadios biológicos para BioCLIP 2.5
BIOLOGICAL_STAGE_PROMPTS: Dict[str, Dict[str, str]] = {
    "adulto": {
        "name": "Adulto",
        "description": "Adulto móvil con alas franjeadas y cuerpo alargado pardo o amarillento",
        "prompt": (
            "A macroscopic photo of an adult thrips insect (Frankliniella occidentalis or Thrips tabaci), "
            "elongated slender dark amber or brown body with long narrow fringed feathered wings "
            "and visible segmented antennae resting on plant leaf or flower petal."
        )
    },
    "ninfa_2": {
        "name": "Larva / Ninfa II (Segundo Estadio)",
        "description": "Ninfa desarrollada color amarillo/anaranjado, ápice cónico, raspador activo",
        "prompt": (
            "A close-up photo of a second instar thrips larva (nymph stage II), "
            "elongated wingless soft body of bright yellow, cream or light orange color, "
            "actively walking and rasping plant tissue or young green fruit surface."
        )
    },
    "ninfa_1": {
        "name": "Larva / Ninfa I (Primer Estadio)",
        "description": "Ninfa diminuta recién nacida (<0.5 mm), translúcida o blanquecina",
        "prompt": (
            "A microscopic or high-magnification macro photo of a first instar thrips larva (nymph stage I), "
            "diminutive translucent whitish or pale yellowish tiny soft body, newly emerged on leaf surface."
        )
    },
    "pupa": {
        "name": "Prepupa / Pupa",
        "description": "Estadio en reposo (pseudopupa), inmóvil con esbozos alares visibles",
        "prompt": (
            "A close-up photo of a thrips prepupa or pupa, inactive non-feeding stage, "
            "pale body with short wing buds or pads visible along thorax and abdomen, resting in crevice or soil."
        )
    },
    "dano_gulupa": {
        "name": "Daño Fitosanitario (Roña / Cacarizado en Fruto o Flor)",
        "description": "Lesión corchosa plateada/parda en fruto verde de Gulupa o deformación de botón",
        "prompt": (
            "Severe thrips feeding damage symptoms on purple passionfruit (gulupa, Passiflora edulis): "
            "corky scab, silvering spots, rough brown scarring (cacarizado, roña) on young green fruit epidermis, "
            "chlorotic stippling and black fecal specks on foliage."
        )
    }
}

# Lista de llaves de trips positivos para calcular la probabilidad acumulada
POSITIVE_TRIPS_KEYS = [
    "trips_frankliniella_occidentalis",
    "trips_frankliniella_panamensis",
    "trips_tabaci",
    "trips_general",
    "trips_dano_fruto_gulupa"
]
