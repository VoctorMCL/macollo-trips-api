# 📖 Diccionario de Datos — Trips BioCLIP 2.5 API

Este documento especifica la totalidad de los modelos de datos, contratos Pydantic, estructuras de intercambio JSON y formatos de almacenamiento en disco utilizados por **Macollo Trips API**.

---

## 1. Modelos de Inferencia y Diagnóstico Fitosanitario

### 1.1 `PredictionResponse` (Respuesta Principal de Diagnóstico)
Entregada por el endpoint `POST /api/predict`.

| Campo | Tipo | Requerido | Descripción | Ejemplo |
| :--- | :--- | :---: | :--- | :--- |
| `is_thrips` | `boolean` | Sí | `true` si la probabilidad combinada de trips o daño directo supera el umbral (`CONFIDENCE_THRESHOLD = 0.60`). | `true` |
| `thrips_confidence` | `float` | Sí | Confianza normalizada ($0.0$ a $1.0$) de la presencia de trips, ajustada por la galería Few-Shot. | `0.9412` |
| `detected_target` | `string` | Sí | Nombre de la especie identificada o de la categoría/confusor detectado. | `"Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)"` |
| `detected_stage` | `string` | Sí | Nombre agronómico de la fase biológica detectada o `"N/A"` si no se detectó trips. | `"Larva (Ninfa)"` |
| `stage_confidence` | `float` | Sí | Certeza normalizada ($0.0$ a $1.0$) en la asignación del estadio específico. | `0.8954` |
| `is_damage_manifestation` | `boolean` | Sí | `true` si la detección corresponde a lesiones de roña/cacarizado en fruto o flor. | `false` |
| `cycle_info` | `CycleInfo` o `null` | No | Estimación fenológica en función de la temperatura del invernadero. | Objeto `CycleInfo` |
| `recommendations` | `AgronomicRecommendations` o `null` | No | Plan fitosanitario estructurado de Manejo Integrado de Plagas (MIP). | Objeto `AgronomicRecommendations` |
| `exemplar_matches` | `List[ExemplarMatch]` | Sí | Lista de hasta $k=3$ fotos coincidentes de la galería local con su similitud de cosenos. | `[...]` |
| `diagnostics` | `object` | Sí | Metadatos técnicos de ejecución del Vision Transformer y parámetros de inferencia. | `{"model_used": "...", ...}` |
| `inference_time_ms` | `float` | Sí | Tiempo total de cómputo en milisegundos desde la recepción del archivo hasta el JSON final. | `328.45` |

---

### 1.2 `CycleInfo` (Modelo Térmico de Grados-Día)
Sub-objeto contenido dentro de `PredictionResponse.cycle_info`.

| Campo | Tipo | Requerido | Descripción | Ejemplo |
| :--- | :--- | :---: | :--- | :--- |
| `temperature_c` | `float` | Sí | Temperatura ambiental (°C) tomada en cuenta para la proyección biológica. | `22.5` |
| `detected_stage_key` | `string` | Sí | Clave corta de la fase: `"huevo"`, `"larva"`, `"pupa"`, `"adulto"`, `"dano_gulupa"`. | `"larva"` |
| `detected_stage_name` | `string` | Sí | Nombre agronómico descriptivo de la fase actual. | `"Larva / Ninfa (Fase de Raspado)"` |
| `current_stage_duration_days` | `string` | Sí | Estimación de duración de la fase actual en días a la temperatura indicada. | `"7.9 días a 22.5°C"` |
| `days_to_adult` | `string` | Sí | Días proyectados restantes para la emergencia de la siguiente cohorte de adultos. | `"4.6 días (pasará a pupa y luego a adulto)"` |
| `urgency_level` | `string` | Sí | Nivel de riesgo agronómico: `"BAJO"`, `"MODERADO"`, `"ALTO"`, `"CRÍTICO"`. | `"CRÍTICO"` |
| `urgency_rationale` | `string` | Sí | Justificación agronómica detallada del riesgo para el cultivo de Gulupa. | `"La larva (ninfa) es el estadio con mayor consumo alimenticio..."` |

---

### 1.3 `AgronomicRecommendations` (Plan Fitosanitario MIP)
Sub-objeto contenido dentro de `PredictionResponse.recommendations`.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `biological_control` | `List[string]` | Sí | Protocolos de liberación de macroorganismos (ácaros/chinches depredadores) y bioinsumos microbianos (*Beauveria*). |
| `ethological_control` | `List[string]` | Sí | Directrices de trampas cromotrópicas adhesivas azules (~460 nm), densidad por m² y umbrales de acción. |
| `cultural_control` | `List[string]` | Sí | Prácticas de espaldera, podas sanitarias, ventilación, humedad relativa y erradicación de malezas reservorio. |
| `chemical_biorational_control` | `List[string]` | Sí | Opciones biorracionales (jabón potásico + neem) e insecticidas de contacto/ingestión con rotación estricta IRAC. |
| `export_impact_alert` | `string` | Sí | Advertencia sobre tolerancia cero de roña/cacarizado en fruta de exportación según normativas GlobalG.A.P. |

---

### 1.4 `ExemplarMatch` (Coincidencia con Fotos de la Finca)
| Campo | Tipo | Requerido | Descripción | Ejemplo |
| :--- | :--- | :---: | :--- | :--- |
| `filename` | `string` | Sí | Nombre del archivo de fotografía guardado en el servidor. | `"1729758120_ninfa_lote1.jpg"` |
| `stage` | `string` | Sí | Fase biológica asignada al ejemplar en disco. | `"larva"` |
| `similarity` | `float` | Sí | Similitud de cosenos normalizada en el espacio latente ($0.0$ a $1.0$). | `0.8845` |

---

## 2. Modelos de Autenticación y API Keys

### 2.1 `LoginRequest` y `LoginResponse`
- **`LoginRequest`**:
  - `username` (`string`): Nombre de usuario administrador.
  - `password` (`string`): Contraseña de acceso al panel.
- **`LoginResponse`**:
  - `authenticated` (`boolean`): `true` tras validación exitosa.
  - `username` (`string`): Nombre de usuario validado.

### 2.2 `ApiKeyCreateRequest` y `ApiKeyCreateResponse`
- **`ApiKeyCreateRequest`**:
  - `name` (`string`, 1 a 80 caracteres): Nombre descriptivo para el cliente o finca.
- **`ApiKeyCreateResponse`**:
  - `message` (`string`): Instrucción de seguridad.
  - `raw_key` (`string`): Clave completa con prefijo `mk_` (ej. `mk_3fA9...`). **Solo se muestra una vez**.
  - `key` (`ApiKeyPublic`): Metadatos de la clave registrada.

### 2.3 `ApiKeyPublic`
| Campo | Tipo | Requerido | Descripción | Ejemplo |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `string` | Sí | Identificador hexadecimal único de 16 caracteres. | `"f89a12c45e678901"` |
| `name` | `string` | Sí | Nombre descriptivo asignado. | `"Integración Astro Portal"` |
| `key_prefix` | `string` | Sí | Primeros 12 caracteres visibles de la clave para auditoría. | `"mk_aBcDeFgHiJ"` |
| `created_at` | `string` | Sí | Marca temporal de creación en formato ISO-8601 UTC. | `"2026-10-24T08:30:00Z"` |
| `created_by` | `string` | Sí | Usuario que generó la clave. | `"admin"` |
| `last_used_at` | `string` o `null` | No | Último acceso registrado con éxito. | `"2026-10-24T09:42:15Z"` |
| `active` | `boolean` | Sí | `true` si la clave está autorizada; `false` si ha sido revocada. | `true` |

---

## 3. Formato y Esquemas de Almacenamiento en Disco

```text
data/
├── .auth_secret                    # 32 bytes de entropía pura para firma HMAC-SHA256 (chmod 0600)
├── api_keys.json                   # Arreglo JSON de claves registradas (hashes SHA-256) (chmod 0600)
├── gallery_embeddings.pt           # Checkpoint binario PyTorch con embeddings latentes y metadatos
└── reference_gallery/              # Estructura física de fotografías organizadas por fase
    ├── huevo/                      # Fotos de huevos de trips o inserciones
    ├── larva/                      # Fotos de larvas / ninfas activas de trips
    ├── pupa/                       # Fotos de pupas / prepupas en reposo
    ├── adulto/                     # Fotos de trips adultos con alas franjeadas
    └── dano_gulupa/                # Fotos de roña / cacarizado en frutos verdes
```

### 3.1 Estructura del Checkpoint `gallery_embeddings.pt`
Guardado mediante `torch.save()`:
```python
{
    "embeddings": torch.Tensor,  # Tensor float32 de forma [N, 1024] normalizado en norma L2
    "metadata": [
        {
            "filename": str,      # Nombre del archivo en disco
            "stage": str,         # Fase biológica ("huevo", "larva", "pupa", "adulto", "dano_gulupa")
            "path": str           # Ruta absoluta en el sistema de archivos
        },
        ...
    ]
}
```
