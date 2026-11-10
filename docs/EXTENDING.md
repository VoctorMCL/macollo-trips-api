# 🧩 Extender el catálogo — nuevas plagas, moscas y arañas rojas

La versión 2.x separa el **conocimiento agronómico** (qué se detecta y cómo se
maneja) del **motor de machine learning** (cómo se calculan los embeddings y se
compara la imagen). Añadir un objetivo nuevo ya no requiere tocar el motor, la
API ni la interfaz: basta con registrar datos en el catálogo.

```
backend/app/domain/catalog.py   ← perfiles, objetivos, estadios y carpetas de galería
backend/app/agronomy/           ← ciclo térmico y recomendaciones MIP por perfil
backend/app/ml/                 ← motor genérico (no suele modificarse)
backend/app/api/                ← rutas genéricas (no suele modificarse)
frontend/src/                   ← UI dirigida por /api/profiles y /api/catalog
```

---

## 1. Conceptos

| Concepto | Qué representa | Ejemplo |
| :--- | :--- | :--- |
| **Perfil** (`DetectionProfile`) | Grupo de clases que se clasifican juntas y su umbral de decisión. | `trips`, `moscas`, `aranas_rojas` |
| **Objetivo** (`DetectionTarget`) | Una clase visual: plaga, daño, tejido sano o clase de rechazo. | `mosca_frutal_anastrepha`, `arana_roja_tetranychus` |
| **Estadio** (`StageDefinition`) | Fase biológica de la plaga. | `larva`, `adulto` |
| **Etiqueta de galería** (`GalleryLabel`) | Carpeta física donde viven las fotos de referencia. | `moscas/mosca_frutal_anastrepha/adulto` |

Un perfil declara:

- `target_keys`: todas las clases que compiten en el softmax.
- `positive_target_keys`: las que cuentan como “detección positiva”.
- `stages`: estadios válidos.
- `min_confidence` y `min_margin`: calibración de la decisión.
- `damage_stage_keys`: estadios que representan daño visible.
- `experimental`: avisa en API y UI de que falta calibración con fotos reales.

---

## 2. Añadir una plaga a un perfil existente

### 2.1 Registrar el objetivo

En `backend/app/domain/catalog.py`, dentro del bloque de `_register(...)` que
corresponda:

```python
DetectionTarget(
    key="mosca_negra_fungus_gnat",
    common_name="Mosca Negra del Sustrato",
    scientific_name="Bradysia spp.",
    kind=KIND_PEST,  # pest | damage | healthy | other
    description="Adultos pequeños y oscuros; larvas en sustrato húmedo.",
    prompts=(
        "a close-up photo of a dark fungus gnat adult on a yellow sticky trap",
        "a macro photo of Bradysia fungus gnat on a greenhouse crop leaf",
        "a small black fly resting on a plant stem in a greenhouse",
    ),
),
```

Reglas prácticas para los prompts:

1. Describe **lo que ve la cámara**, no la etiqueta taxonómica aislada.
2. Incluye 2–4 variantes (plano, hospedero, trampa, síntoma) para el ensamble.
3. Mantén el mismo idioma y estilo en todas las clases del perfil.
4. Añade siempre clases de rechazo (`neg_...`, `sano`, `otro`) para evitar
   falsos positivos por eliminación.

### 2.2 Añadirlo al perfil

```python
MOSCAS_PROFILE = DetectionProfile(
    ...
    target_keys=tuple(k for k in TARGETS if k.startswith("mosca_")),  # ya lo incluye
    positive_target_keys=(
        "mosca_frutal_anastrepha",
        "mosca_negra_fungus_gnat",  # nuevo
    ),
    ...
)
```

El motor, el endpoint `/api/profiles`, la galería y la UI recogen el cambio
automáticamente. Las carpetas de galería se generan como
`data/reference_gallery/moscas/mosca_negra_fungus_gnat/<estadio>/`.

### 2.3 Ajustar el manejo agronómico (opcional)

Si el objetivo necesita recomendaciones propias, amplía
`backend/app/agronomy/flies.py` o `mites.py`. Si el perfil es nuevo, registra
un proveedor en `backend/app/agronomy/registry.py`:

```python
if profile_key == "acaros":
    cycle = get_mite_cycle_estimate(stage_key, temperature_c)
    recommendations = get_mite_mip_recommendations(stage_key)
    return cycle, recommendations
```

El contrato esperado es:

```python
cycle_info = {
    "temperature_c": 22.0,
    "detected_stage_key": "adulto",
    "detected_stage_name": "Adulto",
    "current_stage_duration_days": "…",
    "days_to_adult": "…",
    "urgency_level": "MODERADO",  # CRÍTICO | ALTO | MODERADO | BAJO
    "urgency_rationale": "…",
}

recommendations = {
    "biological_control": [...],
    "ethological_control": [...],
    "cultural_control": [...],
    "chemical_biorational_control": [...],
    "export_impact_alert": "…",
}
```

---

## 3. Crear un perfil completamente nuevo

```python
ACAROS_STAGES = {
    "huevo": StageDefinition(
        key="huevo",
        name="Huevo",
        description="Huevos esféricos sobre el envés.",
        prompts=("a macro photo of mite eggs on the underside of a leaf",),
    ),
    "adulto": StageDefinition(
        key="adulto",
        name="Adulto",
        description="Ácaros móviles y telaraña fina.",
        prompts=("a macro photo of an adult mite and fine webbing on a leaf",),
    ),
}

ACAROS_PROFILE = DetectionProfile(
    key="acaros",
    name="Ácaros",
    description="Detección de arañita roja y ácaro plano en gulupa.",
    crop="gulupa",
    target_keys=("acaro_arania_roja", "acaro_plano", "neg_hoja_sana"),
    positive_target_keys=("acaro_arania_roja", "acaro_plano"),
    stages=ACAROS_STAGES,
    min_confidence=0.60,
    min_margin=0.05,
    experimental=True,
    agronomy_provider="generic_mites",
)

PROFILES = {
    profile.key: profile
    for profile in (TRIPS_PROFILE, MOSCAS_PROFILE, ARANAS_ROJAS_PROFILE, ACAROS_PROFILE)
}
```

Después:

1. Añade el proveedor agronómico en `registry.py`.
2. Reinicia la API (los prototipos de texto se precalculan al cargar el modelo).
3. Comprueba `GET /api/profiles/acaros`.
4. Sube fotos reales y calibra el umbral antes de quitar `experimental=True`.

---

## 4. Galería de referencia (few-shot)

### Estructura en disco

```
data/reference_gallery/
├── huevo/                 # trips histórico
├── larva/
├── pupa/
├── adulto/
├── dano_gulupa/
├── moscas/
│   └── mosca_frutal_anastrepha/
│       ├── huevo/
│       ├── larva/
│       ├── pupa/
│       ├── adulto/
│       └── dano/
└── aranas_rojas/
    └── arana_roja_tetranychus/
        ├── huevo/
        ├── larva/
        ├── adulto/
        └── dano/
```

- La subida desde la web usa `label` (recomendado) o los campos históricos
  `stage`/`profile`/`target`.
- `GET /api/gallery/labels` devuelve las claves válidas agrupadas por perfil.
- El índice (`data/gallery_embeddings.pt`) guarda una firma de archivos; si una
  foto cambia, `/api/health` marca `gallery.is_stale` y la predicción puede
  reindexar automáticamente al cargar el modelo.

### Calibración recomendada

1. Reúne al menos 15–30 fotos por clase y estadio, con variedad de luz, fondo y
   distancia.
2. Mantén ejemplos de las clases de rechazo (hoja sana, trampa vacía, sombra).
3. Usa `diagnostics.margin` y `detection.is_uncertain` para detectar clases
   confundibles.
4. Ajusta `min_confidence`/`min_margin` del perfil con un conjunto de validación
   propio; no los cambies solo con impresiones visuales.
5. Cuando el perfil supere la validación de campo, pon `experimental=False`.

---

## 5. Variables de entorno relevantes

| Variable | Defecto | Uso |
| :--- | :--- | :--- |
| `DEFAULT_DETECTION_PROFILE` | `trips` | Perfil sugerido por la API y la UI. |
| `CONFIDENCE_THRESHOLD` | `0.60` | Umbral del perfil `trips` (compatibilidad 1.x); los perfiles nuevos usan su `min_confidence`. |
| `KNN_TOP_K` | `5` | Vecinos usados en la votación de galería. |
| `GALLERY_MIN_SIMILARITY` | `0.62` | Similitud mínima para aportar evidencia. |
| `GALLERY_MAX_BOOST` | `0.15` | Refuerzo máximo de confianza por galería. |
| `ENABLE_TTA` | `false` | Test-time augmentation por defecto. |
| `MAX_UPLOAD_BYTES` | `15728640` | Tamaño máximo de subida (15 MB). |

---

## 6. Compatibilidad 1.x

- `profile` es opcional y por defecto `trips`.
- `is_thrips` y `thrips_confidence` se mantienen; solo se rellenan con el perfil
  `trips`.
- `detected_target`, `detected_stage`, `stage_confidence`, `cycle_info`,
  `recommendations`, `exemplar_matches` y `diagnostics` se mantienen.
- Las carpetas de galería `huevo`, `larva`, `pupa`, `adulto` y `dano_gulupa`
  siguen siendo válidas.

Los clientes nuevos deben leer `profile`, `crop` y `detection` en lugar de
inferir el tipo de plaga desde `is_thrips`.

---

## 7. Checklist para una nueva clase

- [ ] `DetectionTarget` registrado con prompts variados y `kind` correcto.
- [ ] Incluido en `target_keys` y, si aplica, `positive_target_keys` del perfil.
- [ ] Estadios definidos con prompts.
- [ ] Proveedor agronómico devuelve `cycle_info` y `recommendations`.
- [ ] Carpetas de galería creadas y `.gitignore` actualizado si es necesario.
- [ ] `backend/tests/test_catalog.py` ampliado si cambia el contrato.
- [ ] `GET /api/profiles` y `GET /api/handbook?profile=...` responden.
- [ ] Predicción real verificada con una foto de ejemplo.
- [ ] Umbral calibrado y `experimental=False` solo tras validación de campo.
