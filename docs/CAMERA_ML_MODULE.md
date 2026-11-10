# 📸 Módulo de Detección con Cámara y Machine Learning

> Documentación técnica del sistema de visión artificial BioCLIP 2.5 para identificación fitosanitaria en cultivos de Gulupa (*Passiflora edulis*).

> [!NOTE]
> **Documento histórico.** Este archivo describe el módulo original centrado en
> trips y se conserva por contexto. La referencia vigente y completa está en
> [Arquitectura](./ARCHITECTURE.md), [Endpoints](./ENDPOINTS.md) y
> [Extender el Catálogo](./EXTENDING.md). La versión 2.x es genérica por perfil:
> `trips`, `moscas` y `aranas_rojas`.

---

## 1. Descripción General

Este módulo es una **API REST independiente** (Python + FastAPI) que recibe una foto tomada desde el celular y determina:

1. **¿Hay trips en la imagen?** — Sí/No con nivel de confianza.
2. **¿En qué fase biológica está?** — Huevo, Larva (Ninfa), Pupa o Adulto (además de Daño visible).
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
macollo-trips-api/
├── backend/
│   └── app/
│       ├── config.py                  # Configuración: umbrales, rutas, modelo
│       ├── main.py                    # API FastAPI (routers + CORS + estáticos)
│       ├── auth.py                    # Login, sesiones y API keys
│       ├── api/
│       │   ├── auth_routes.py         # /api/auth/*, /api/keys/*
│       │   ├── health_routes.py       # /api/health
│       │   ├── catalog_routes.py      # /api/catalog, /profiles, /handbook
│       │   ├── gallery_routes.py      # /api/gallery/*
│       │   └── prediction_routes.py   # /api/predict
│       ├── domain/
│       │   └── catalog.py             # Perfiles, objetivos, estadios y galería
│       ├── ml/
│       │   ├── bioclip_engine.py      # Motor de inferencia BioCLIP 2.5
│       │   ├── prompt_bank.py         # Ensamble de prompts por clase
│       │   ├── taxonomy_prompts.py    # Compatibilidad de prompts
│       │   └── gallery_index.py       # Galería de referencia (Few-Shot k-NN)
│       ├── agronomy/
│       │   ├── registry.py            # Despacho por perfil
│       │   ├── gulupa_cycle.py        # Modelo térmico de trips (grados-día)
│       │   ├── gulupa_mip.py          # Recomendaciones MIP de trips
│       │   ├── flies.py               # Ciclo y MIP de mosca de la fruta
│       │   └── mites.py               # Ciclo y MIP de araña roja
│       ├── services/
│       │   └── images.py              # Validación y orientación EXIF
│       └── schemas/
│           ├── __init__.py
│           └── prediction.py          # Modelos Pydantic (request/response)
│   └── tests/
│       ├── test_api.py                # Endpoints HTTP y seguridad
│       ├── test_ml_pipeline.py        # Agronomía, prompts y criptografía
│       └── test_catalog.py            # Catálogo y API genérica
├── frontend/                          # Web App React + Vite (servida por FastAPI)
│   ├── src/components/
│   └── dist/
├── data/
│   └── reference_gallery/
│       ├── huevo/ ... dano_gulupa/    # Carpetas históricas de trips
│       ├── moscas/mosca_frutal_anastrepha/...
│       └── aranas_rojas/arana_roja_tetranychus/...
├── client_example.js                  # Snippet de integración para tu web
├── requirements.txt                   # Dependencias Python
├── run_server.sh                      # Script de arranque
└── .gitignore
```

### 2.2 Componentes Principales

| Componente | Archivo | Responsabilidad |
|---|---|---|
| **API REST** | `api/*.py` | Routers HTTP, CORS, validación de archivos |
| **Autenticación** | `auth.py` | Login de panel, sesiones firmadas y API keys |
| **Catálogo** | `domain/catalog.py` | Perfiles, objetivos, estadios y etiquetas de galería |
| **Motor BioCLIP** | `ml/bioclip_engine.py` | Carga del modelo, embeddings y pipeline de inferencia |
| **Prompts** | `ml/prompt_bank.py` | Ensamble de descripciones por objetivo y estadio |
| **Galería k-NN** | `ml/gallery_index.py` | Indexación y búsqueda filtrada por perfil |
| **Agronomía** | `agronomy/registry.py` | Despacho a `gulupa_trips`, `fruit_flies` o `red_spider_mites` |
| **Ciclo y MIP** | `agronomy/gulupa_cycle.py`, `gulupa_mip.py`, `flies.py`, `mites.py` | Modelo térmico y recomendaciones por perfil |
| **Schemas** | `schemas/prediction.py` | Modelos Pydantic para el JSON |

---

## 3. API REST — Endpoints

> El panel web tiene login y **no tiene registro público**. Las fotos y la gestión de claves
> requieren sesión; `/api/predict` acepta una sesión web válida o una API key en `X-API-Key`.

### 3.0 Autenticación

- `POST /api/auth/login` — credenciales del servidor (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- `POST /api/auth/logout` — cierra la sesión.
- `GET /api/auth/me` — usuario autenticado.
- `GET /api/keys` — lista claves (sesión).
- `POST /api/keys` — crea una clave; el valor completo se muestra una sola vez.
- `DELETE /api/keys/{id}` — revoca una clave.

Variables de entorno recomendadas en producción: `ADMIN_USERNAME`, `ADMIN_PASSWORD`,
`AUTH_SECRET_KEY`, `SESSION_COOKIE_SECURE=true`.

### 3.1 `GET /api/health`

Verifica el estado del servicio.

**Respuesta:**
```json
{
  "status": "healthy",
  "app_name": "Macollo Visión Fitosanitaria API",
  "version": "2.0.0",
  "model_loaded": true,
  "model_name": "hf-hub:imageomics/bioclip-2.5-vith14",
  "device": "cpu",
  "default_profile": "trips",
  "profiles": [
    {"key": "trips", "name": "Trips", "experimental": false},
    {"key": "moscas", "name": "Moscas de la Fruta", "experimental": false},
    {"key": "aranas_rojas", "name": "Arañas Rojas", "experimental": false}
  ],
  "gallery_total_images": 0,
  "gallery_is_indexed": false,
  "gallery_is_stale": false
}
```

### 3.2 `POST /api/predict` ⭐ Endpoint principal

Recibe una foto y devuelve el diagnóstico fitosanitario completo.
Requiere el encabezado `X-API-Key: mk_...` (o una sesión web válida).

**Request** (`multipart/form-data`):

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | `File` | ✅ | Foto JPG/PNG/WebP/BMP tomada con la cámara |
| `temperature_c` | `float` | ❌ (default 20.0) | Temperatura del invernadero en °C |
| `crop` | `string` | ❌ (default "gulupa") | Cultivo analizado |
| `profile` | `string` | ❌ (default "trips") | `trips`, `moscas` o `aranas_rojas` |
| `use_tta` | `bool` | ❌ | Test-time augmentation (más preciso, más lento) |

**Respuesta** (`application/json`):
```json
{
  "profile": "trips",
  "crop": "gulupa",
  "is_thrips": true,
  "thrips_confidence": 0.87,
  "detected_target": "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)",
  "detected_stage": "Larva (Ninfa)",
  "stage_confidence": 0.82,
  "is_damage_manifestation": false,
  "cycle_info": {
    "temperature_c": 22.0,
    "detected_stage_key": "larva",
    "detected_stage_name": "Larva / Ninfa (Fase de Raspado)",
    "current_stage_duration_days": "8.3 días a 22.0°C",
    "days_to_adult": "5.0 días (pasará a prepupa/pupa y luego a adulto)",
    "urgency_level": "CRÍTICO",
    "urgency_rationale": "La larva (ninfa) es el estadio con mayor consumo alimenticio..."
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

Estado de la galería de referencia (conteo de fotos por estadio). Requiere sesión.

### 3.4 `POST /api/gallery/upload`

Sube una foto de referencia. Campos: `file` (imagen) y `label` (recomendado, ver `GET /api/gallery/labels`) o `profile` + `target` + `stage`. Requiere sesión.

### 3.5 `GET /api/gallery/labels`

Lista las carpetas válidas agrupadas por perfil. Requiere sesión. Acepta `?profile=trips|moscas|aranas_rojas`.

### 3.6 `POST /api/gallery/reindex`

Fuerza la reindexación de todas las fotos en `data/reference_gallery/`. Requiere sesión.

### 3.7 `GET /api/handbook`

Ficha técnica genérica por perfil. Parámetros opcionales: `profile` y `temperature_c`. El alias histórico `GET /api/gulupa-handbook` se conserva para trips.

### 3.8 Documentación Interactiva (Swagger)

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

BioCLIP compara el embedding de la imagen contra los prototipos de texto del **perfil seleccionado**. El motor ya no usa una lista fija de 14 prompts: cada perfil define sus objetivos y estadios en `domain/catalog.py`, y `prompt_bank.py` promedia los embeddings de sus descripciones.

Para el perfil `trips`, las clases positivas son:
- `Frankliniella occidentalis` (trips de las flores)
- `Frankliniella panamensis` (trips de pasifloras)
- `Thrips tabaci` (trips de la cebolla)
- Trips general
- Daño de trips en fruto de Gulupa

Las clases negativas incluyen mosca blanca, pulgón, araña roja, ácaro plano, mosca minadora, hoja/flor sana, tallo/zarcillo y manchas de polvo/caldo.

La probabilidad acumulada de las clases positivas debe superar el **umbral del perfil** (0.60 por defecto) para confirmar el objetivo.

### 4.2 Paso 4: Clasificación de Estadio

Si es trips, se clasifica en una de las 4 fases biológicas (más la categoría de daño):

| Estadio | Descripción | Nivel de Urgencia |
|---|---|---|
| **Huevo** | Ovalado y translúcido, insertado en el tejido | ALTO |
| **Larva (Ninfa)** | Único estadio larval, sin alas; raspado voraz → cacarizado | CRÍTICO |
| **Pupa** | En reposo, esbozos alares visibles | ALTO |
| **Adulto** | Con alas franjeadas, fase reproductora | CRÍTICO |
| **Daño** | Roña/cacarizado en fruto, lesión irreversible (no es una fase) | CRÍTICO |

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
PUBLIC_TRIPS_API_KEY=mk_tu_clave_generada_en_el_panel
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
    headers: { "X-API-Key": import.meta.env.PUBLIC_TRIPS_API_KEY },
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
    headers: { "X-API-Key": process.env.TRIPS_API_KEY ?? "" },
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
cd /home/victormcl/Documents/macollo-trips-api
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
cd /home/victormcl/Documents/macollo-trips-api
source .venv/bin/activate
python -m unittest discover -s backend/tests -v
```

**23 tests cubiertos:**
- Endpoints HTTP, autenticación, API keys y validación de subidas.
- Catálogo extensible, perfiles y etiquetas de galería.
- Integridad de prompts, ciclo térmico y recomendaciones MIP por perfil.
- Inicialización y reindexación de la galería.
- Resistencia a manipulación de tokens de sesión.

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
| `CONFIDENCE_THRESHOLD` | `0.60` | Umbral mínimo para confirmar el objetivo |
| `DEFAULT_TEMPERATURE_C` | `20.0` | Temperatura por defecto si no se envía |
| `DEFAULT_DETECTION_PROFILE` | `trips` | Perfil usado cuando no se envía `profile` |
| `KNN_TOP_K` | `5` | Vecinos más cercanos en galería |
| `STAGES` | 4 fases + daño | Carpetas históricas de trips: `huevo`, `larva`, `pupa`, `adulto`, `dano_gulupa` |

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
Description=Macollo Visión Fitosanitaria API
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
| El resultado no corresponde al perfil | No se envió `profile` o la galería está en otra carpeta | Enviar `profile` y subir fotos con el `label` correcto |
| Lento (~2s/imagen) | CPU sin GPU | Normal; usar GPU para <200ms |
| Se cae por memoria | Múltiples workers | Usar `--workers 1` y ≥8 GB RAM |
