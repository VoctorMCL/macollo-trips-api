# 📸 Módulo de Detección de Trips con Cámara y Machine Learning

> Documentación técnica del sistema de visión artificial BioCLIP 2.5 para identificación de Trips (*Thysanoptera: Thripidae*) en cultivos de Gulupa (*Passiflora edulis*).

---

## 1. Descripción General

Este módulo es una **API REST independiente** (Python + FastAPI) que recibe una foto tomada desde el celular y determina:

1. **¿Hay trips en la imagen?** — Sí/No con nivel de confianza.
2. **¿En qué estadio biológico está?** — Adulto, Ninfa I, Ninfa II, Pupa o Daño visible.
3. **¿Cuánto falta para que se vuelva adulto?** — Cálculo basado en grados-día y temperatura del invernadero.
4. **¿Qué hacer?** — Recomendaciones de Manejo Integrado de Plagas (MIP) específicas para Gulupa de exportación.

### Modelo de IA: BioCLIP 2.5

El motor de inferencia usa **BioCLIP 2.5** (`imageomics/bioclip-2.5-vith14`), un modelo de fundación biológica basado en la arquitectura **ViT-H/14** (Vision Transformer Huge) entrenado con el framework [OpenCLIP](https://github.com/mlfoundations/open_clip) sobre el dataset TreeOfLife-10M de iNaturalist.

- **Tipo de modelo**: Zero-shot contrastivo (imagen ↔ texto), no requiere re-entrenamiento.
- **Enfoque**: Taxonomía biológica — diseñado específicamente para identificar organismos vivos.
- **Tamaño**: ~4 GB de pesos (se descargan automáticamente desde HuggingFace Hub).
- **Dispositivo**: CPU (funcional) o GPU CUDA (más rápido).

```text
Navegador (celular)                   API FastAPI + BioCLIP 2.5
       │                                      │
       │  POST /api/predict                   │
       │  (foto + temperatura)                │
       ├─────────────────────────────────────→ │
       │                                      ├── 1. Extraer vector de imagen (1024 dim)
       │                                      ├── 2. Comparar vs prompts taxonómicos
       │                                      ├── 3. Clasificar estadio biológico
       │                                      ├── 4. Buscar en galería de referencia (k-NN)
       │                                      ├── 5. Calcular ciclo térmico (grados-día)
       │                                      └── 6. Generar recomendaciones MIP
       │  ←──────────────────────────────────  │
       │  JSON con diagnóstico completo       │
```

---

## 2. Arquitectura del Módulo

### 2.1 Estructura de Archivos

```text
Macollo/
├── backend/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                  # Configuración: umbrales, rutas, modelo
│   │   ├── main.py                    # API FastAPI (endpoints REST + CORS)
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── bioclip_engine.py      # Motor de inferencia BioCLIP 2.5
│   │   │   ├── taxonomy_prompts.py    # Prompts taxonómicos para zero-shot
│   │   │   └── gallery_index.py       # Galería de referencia (Few-Shot k-NN)
│   │   ├── agronomy/
│   │   │   ├── __init__.py
│   │   │   ├── gulupa_cycle.py        # Modelo térmico (grados-día)
│   │   │   └── gulupa_mip.py          # Recomendaciones MIP
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── prediction.py          # Modelos Pydantic (request/response)
│   └── tests/
│       ├── __init__.py
│       ├── test_api.py                # Tests de endpoints HTTP
│       └── test_ml_pipeline.py        # Tests de taxonomía, ciclo y galería
├── frontend/                          # Web App demo (NO es parte de Proyect_invernadero)
│   ├── index.html
│   ├── css/style.css
│   └── js/ (app.js, camera.js, gallery.js)
├── data/
│   └── reference_gallery/             # Fotos reales del usuario por estadio
│       ├── adulto/
│       ├── ninfa_1/
│       ├── ninfa_2/
│       ├── pupa/
│       └── dano_gulupa/
├── client_example.js                  # Snippet de integración para tu web
├── requirements.txt                   # Dependencias Python
├── run_server.sh                      # Script de arranque
└── .gitignore
```

### 2.2 Componentes Principales

| Componente | Archivo | Responsabilidad |
|---|---|---|
| **API REST** | `main.py` | Endpoints HTTP, CORS, validación de archivos |
| **Motor BioCLIP** | `bioclip_engine.py` | Carga del modelo, extracción de embeddings, pipeline de inferencia completo |
| **Prompts Taxonómicos** | `taxonomy_prompts.py` | Descripciones textuales de trips y organismos confusores para zero-shot |
| **Galería k-NN** | `gallery_index.py` | Indexación y búsqueda de fotos de referencia del usuario |
| **Ciclo Térmico** | `gulupa_cycle.py` | Cálculo de duración de cada estadio según temperatura (grados-día) |
| **MIP Gulupa** | `gulupa_mip.py` | Recomendaciones fitosanitarias por estadio detectado |
| **Schemas** | `prediction.py` | Modelos Pydantic para serialización/validación del JSON |

---

## 3. API REST — Endpoints

### 3.1 `GET /api/health`

Verifica el estado del servicio.

**Respuesta:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "hf-hub:imageomics/bioclip-2.5-vith14",
  "device": "cpu",
  "gallery_total_images": 0,
  "gallery_is_indexed": false
}
```

### 3.2 `POST /api/predict` ⭐ Endpoint principal

Recibe una foto y devuelve el diagnóstico fitosanitario completo.

**Request** (`multipart/form-data`):

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | `File` | ✅ | Foto JPG/PNG/WebP tomada con la cámara |
| `temperature_c` | `float` | ❌ (default 20.0) | Temperatura del invernadero en °C |
| `crop` | `string` | ❌ (default "gulupa") | Cultivo analizado |

**Respuesta** (`application/json`):
```json
{
  "is_thrips": true,
  "thrips_confidence": 0.87,
  "detected_target": "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)",
  "detected_stage": "Larva / Ninfa II (Fase de Raspado Voraz)",
  "stage_confidence": 0.82,
  "is_damage_manifestation": false,
  "cycle_info": {
    "temperature_c": 22.0,
    "detected_stage_key": "ninfa_2",
    "detected_stage_name": "Larva / Ninfa II (Fase de Raspado Voraz)",
    "current_stage_duration_days": "5.5 días a 22.0°C",
    "days_to_adult": "5.0 días (pasará a prepupa/pupa y luego a adulto)",
    "urgency_level": "CRÍTICO",
    "urgency_rationale": "La Ninfa II es el estadio con mayor consumo alimenticio..."
  },
  "recommendations": {
    "biological_control": ["..."],
    "ethological_control": ["..."],
    "cultural_control": ["..."],
    "chemical_biorational_control": ["..."],
    "export_impact_alert": "ALERTA GULUPA EXPORTACIÓN: ..."
  },
  "exemplar_matches": [],
  "inference_time_ms": 1400.5
}
```

### 3.3 `GET /api/gallery`

Estado de la galería de referencia (conteo de fotos por estadio).

### 3.4 `POST /api/gallery/upload`

Sube una foto de referencia. Campos: `file` (imagen), `stage` (uno de: `adulto`, `ninfa_1`, `ninfa_2`, `pupa`, `dano_gulupa`).

### 3.5 `POST /api/gallery/reindex`

Fuerza la reindexación de todas las fotos en `data/reference_gallery/`.

### 3.6 `GET /api/gulupa-handbook`

Manual técnico de trips en Gulupa. Parámetro opcional: `temperature_c`.

### 3.7 Documentación Interactiva (Swagger)

Al correr el servidor, abre `http://localhost:8000/docs` para probar todos los endpoints visualmente.

---

## 4. Pipeline de Inferencia (Detalle Técnico)

```
Foto del celular
       │
       ▼
┌──────────────────────────────────────┐
│ 1. Preprocesamiento (PIL → Tensor)   │
│    Resize + Normalize para ViT-H/14  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ 2. Extracción de Embedding           │
│    model.encode_image → vector 1024d │
│    L2-normalize                      │
└──────────────┬───────────────────────┘
               │
       ┌───────┼───────────────┐
       ▼       ▼               ▼
┌────────┐ ┌──────────┐  ┌──────────────┐
│ Paso 3 │ │ Paso 4   │  │ Paso 5       │
│ Zero-  │ │ Estadio  │  │ Galería      │
│ Shot   │ │ Biológ.  │  │ k-NN (opt.)  │
│ Target │ │          │  │              │
└───┬────┘ └────┬─────┘  └──────┬───────┘
    │           │               │
    ▼           ▼               ▼
  is_thrips   detected_stage   gallery_boost
  + confianza + confianza      + voted_stage
       │           │               │
       └───────────┼───────────────┘
                   ▼
┌──────────────────────────────────────┐
│ 6. Motor Agronómico                  │
│    Ciclo térmico + MIP               │
└──────────────────────────────────────┘
                   │
                   ▼
             JSON Response
```

### 4.1 Paso 3: Discriminación Zero-Shot (Trips vs No-Trips)

BioCLIP compara el embedding de la imagen contra **14 prompts taxonómicos** precomputados:

**Clases positivas (5):**
- `Frankliniella occidentalis` (trips de las flores)
- `Frankliniella panamensis` (trips de pasifloras)
- `Thrips tabaci` (trips de la cebolla)
- Trips general
- Daño de trips en fruto de Gulupa

**Clases negativas (9):**
- Mosca blanca, pulgón, araña roja, ácaro plano, mosca minadora
- Hoja sana de Gulupa, flor sana de Gulupa, tallo/zarcillo
- Manchas de polvo/caldo

La probabilidad acumulada de las 5 clases positivas debe superar el **umbral de 0.60** para confirmar trips.

### 4.2 Paso 4: Clasificación de Estadio

Si es trips, se clasifica en uno de 5 estadios:

| Estadio | Descripción | Nivel de Urgencia |
|---|---|---|
| **Adulto** | Con alas franjeadas, fase reproductora | CRÍTICO |
| **Ninfa II** | Amarilla/anaranjada, raspado voraz → cacarizado | CRÍTICO |
| **Ninfa I** | Diminuta (<0.5mm), recién eclosionada | ALTO |
| **Pupa** | En reposo, esbozos alares visibles | ALTO |
| **Daño** | Roña/cacarizado en fruto, lesión irreversible | CRÍTICO |

### 4.3 Paso 5: Galería de Referencia (Few-Shot)

Fotos reales del usuario almacenadas en `data/reference_gallery/` se indexan como vectores BioCLIP. Cuando una nueva foto llega, se buscan los 3 vecinos más cercanos (k-NN por similitud de cosenos). Si el match más cercano supera 0.65 de similitud, aporta un "boost" a la confianza global.

---

## 5. Cómo Conectar desde tu Web (Proyect_invernadero)

### 5.1 Modelo de Conexión

La API de BioCLIP corre como un **servicio separado** (puerto 8000). Tu web Astro (Proyect_invernadero) la consume por HTTP:

```
Tu web Astro (Vercel/VPS)          API BioCLIP (VPS con 8GB+ RAM)
  https://tudominio.com              https://api.tudominio.com
         │                                    │
         │  POST /api/predict                 │
         └───────────────────────────────────→ │
                                               │ BioCLIP 2.5 procesa
         ← JSON ─────────────────────────────  │
```

### 5.2 Opción A: Llamada directa desde el navegador (CORS)

1. **Configura `PUBLIC_API_URL`** en el `.env` de tu proyecto Astro:

```env
PUBLIC_API_URL=https://api.tudominio.com
```

2. **Código JavaScript** en tu componente Astro:

```javascript
const API = import.meta.env.PUBLIC_API_URL || "http://localhost:8000";

const formData = new FormData();
formData.append("file", imagenBlob, "muestra.jpg");
formData.append("temperature_c", "22.5");
formData.append("crop", "gulupa");

const res = await fetch(`${API}/api/predict`, {
    method: "POST",
    body: formData
});
const data = await res.json();
```

### 5.3 Opción B: Proxy desde Astro SSR (sin CORS)

Si tu Astro corre en modo SSR en el mismo servidor que la API, puedes crear un proxy:

```typescript
// src/pages/api/analizar.ts
import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  const entrada = await request.formData();
  const archivo = entrada.get("file");

  if (!(archivo instanceof File)) {
    return new Response(JSON.stringify({ error: "Falta el archivo" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const form = new FormData();
  form.append("file", archivo, archivo.name);
  form.append("temperature_c", String(entrada.get("temperature_c") ?? "20"));
  form.append("crop", "gulupa");

  const res = await fetch("http://127.0.0.1:8000/api/predict", {
    method: "POST",
    body: form,
  });

  return new Response(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
};
```

---

## 6. Cómo Correr el Servidor

### 6.1 Requisitos

- **Python**: 3.10 o superior
- **RAM**: Mínimo 8 GB (el modelo usa ~4 GB)
- **Disco**: ~5 GB para el modelo + dependencias
- **GPU**: Opcional (CUDA). En CPU funciona (~1.4s por imagen)

### 6.2 Instalación

```bash
cd /home/victormcl/Documents/Macollo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.3 Arranque

```bash
# Opción 1: Script automático (incluye IP local para celulares)
./run_server.sh

# Opción 2: Manual
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

La primera ejecución descarga ~4 GB de pesos del modelo desde HuggingFace. Las siguientes cargas son locales (~30-60s).

### 6.4 Verificación

```bash
curl http://localhost:8000/api/health
# Debe mostrar "model_loaded": true
```

### 6.5 Acceso desde el celular (misma red Wi-Fi)

```bash
hostname -I    # Obtener la IP local del PC
# Ejemplo: 192.168.1.50
```

En el celular abrir: `http://192.168.1.50:8000/docs`

---

## 7. Tests

```bash
cd /home/victormcl/Documents/Macollo
source .venv/bin/activate
python -m unittest discover -s backend/tests -v
```

**7 tests cubiertos:**
- `test_health_check`: Endpoint `/api/health` responde 200.
- `test_gallery_endpoints`: Galería responde estadísticas y listado.
- `test_gulupa_handbook_endpoint`: Manual técnico incluye datos de Gulupa.
- `test_taxonomy_prompts_integrity`: Todos los prompts existen y están bien formados.
- `test_thermal_cycle_calculation`: Grados-día a diferentes temperaturas dan resultados coherentes.
- `test_mip_recommendations`: Recomendaciones incluyen las 4 categorías de MIP.
- `test_gallery_manager_initialization`: Galería se inicializa con directorios correctos.

---

## 8. Dependencias

| Paquete | Versión | Propósito |
|---|---|---|
| `fastapi` | ≥0.115 | Framework web async |
| `uvicorn` | ≥0.30 | Servidor ASGI |
| `torch` | ≥2.2 | Backend de tensores para el modelo |
| `torchvision` | ≥0.17 | Transformaciones de imagen |
| `open-clip-torch` | ≥2.24 | Framework OpenCLIP para cargar BioCLIP 2.5 |
| `huggingface-hub` | ≥0.23 | Descarga de pesos del modelo |
| `pillow` | ≥10.2 | Procesamiento de imágenes |
| `pydantic` | ≥2.7 | Validación de datos |
| `python-multipart` | ≥0.0.9 | Parseo de `multipart/form-data` |

---

## 9. Configuración Ajustable

Archivo: `backend/app/config.py`

| Variable | Valor Default | Descripción |
|---|---|---|
| `BIOCLIP_MODEL_NAME` | `hf-hub:imageomics/bioclip-2.5-vith14` | Modelo principal (ViT-H/14) |
| `FALLBACK_MODEL_NAME` | `hf-hub:imageomics/bioclip` | Modelo alternativo (ViT-B/16) si el principal falla |
| `CONFIDENCE_THRESHOLD` | `0.60` | Umbral mínimo para confirmar trips |
| `DEFAULT_TEMPERATURE_C` | `20.0` | Temperatura por defecto si no se envía |
| `KNN_TOP_K` | `3` | Vecinos más cercanos en galería |
| `STAGES` | 5 estadios | `adulto`, `ninfa_1`, `ninfa_2`, `pupa`, `dano_gulupa` |

---

## 10. Despliegue en Producción

### 10.1 Requisitos del Servidor

- Linux (Ubuntu/Debian recomendado)
- ≥8 GB RAM (ideal 12-16 GB)
- Python 3.10+
- Puertos 80/443 abiertos, puerto 8000 **cerrado** al público

### 10.2 Servicio systemd

```ini
[Unit]
Description=Gulupa Trips BioCLIP API
After=network-online.target

[Service]
User=victormcl
WorkingDirectory=/opt/macollo
ExecStart=/opt/macollo/.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> ⚠️ **Un solo worker**: Cada worker cargaría el modelo (~4 GB extra de RAM).

### 10.3 HTTPS con Caddy (recomendado)

```caddyfile
api.tudominio.com {
    reverse_proxy 127.0.0.1:8000
    request_body {
        max_size 20MB
    }
}
```

### 10.4 Restringir CORS en producción

Editar `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tudominio.com",
        "https://www.tudominio.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 11. Solución de Problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `model_loaded: false` | Modelo aún cargando | Esperar 1-2 min, reintentar `/api/health` |
| `Failed to fetch` | API apagada o URL incorrecta | Verificar que uvicorn corre en puerto 8000 |
| Error CORS | Origen no permitido | Revisar `allow_origins` en `main.py` |
| `Mixed Content` | Web HTTPS → API HTTP | Publicar API con HTTPS (Caddy/Nginx) |
| Siempre dice "trips" | Umbral bajo o pocas fotos de referencia | Subir `CONFIDENCE_THRESHOLD` y agregar fotos reales |
| Lento (~2s/imagen) | CPU sin GPU | Normal; usar GPU para <200ms |
| Se cae por memoria | Múltiples workers | Usar `--workers 1` y ≥8 GB RAM |
