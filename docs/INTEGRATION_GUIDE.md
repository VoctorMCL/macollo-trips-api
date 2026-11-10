# 🔌 Guía de Integración para Plataformas y Apps Externas
## Macollo Visión Fitosanitaria API (BioCLIP 2.5)

Esta guía explica cómo conectar cualquier plataforma externa (aplicaciones web en React/Astro/Next.js/Vue, aplicaciones móviles en Flutter/React Native/iOS/Android, microservicios backend en Node.js/Python, o scripts de campo) con la **API de Visión Fitosanitaria de Macollo** desplegada en **Google Cloud Run**.

---

## 1. Arquitectura de Integración

```
┌────────────────────────────────────────────────────────┐
│             TUS APLICACIONES EXTERNAS                  │
│                                                        │
│  [Web Portal / Astro / Next]    [App Móvil Flutter]    │
│  [Sensores IoT / Microservicio] [Scripts Python / Cron]│
└──────────────────────────┬─────────────────────────────┘
                           │
                           │ HTTPS POST /api/predict
                           │ Encabezado: "X-API-Key: mk_live_..."
                           │ Payload: multipart/form-data (foto + temp)
                           ▼
┌────────────────────────────────────────────────────────┐
│               GOOGLE CLOUD RUN (SERVERLESS)            │
│  URL: https://macollo-trips-api-961314735418...        │
│  Dominio: https://macollo.victormcl.me                 │
│                                                        │
│  - FastAPI + Uvicorn (Puerto 8080)                     │
│  - PyTorch + BioCLIP 2.5 (ViT-H/14 - 632M Parámetros)  │
│  - Catálogo Fitosanitario (Trips, Moscas, Arañas)      │
│  - Modelado Grados-Día + Galería de Memoria Few-Shot   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Autenticación con API Key (`X-API-Key`)

Todas las peticiones externas hacia endpoints protegidos (como `/api/predict` y `/api/handbook`) requieren una **API Key estructurada** con prefijo `mk_`.

### 2.1. ¿Cómo generar tu API Key?
1. Entra a la interfaz web de la API:
   * **URL Cloud Run:** `https://macollo-trips-api-961314735418.us-central1.run.app/` (o tu dominio).
2. Inicia sesión con las credenciales de administrador:
   * **Usuario:** `admin` (o tu `ADMIN_USERNAME`)
   * **Contraseña:** `macollo2026` (o tu `ADMIN_PASSWORD`)
3. En la barra superior, haz clic en **«API y accesos»**.
4. En el campo *Etiqueta*, escribe el nombre de la app (ej. `portal-web-produccion` o `app-movil-agronomo`) y haz clic en **«Crear clave»**.
5. Copia la clave generada (ej. `mk_live_8f3a9b1c4e2d7f0a...`).

> [!IMPORTANT]
> Guarda la clave en las variables de entorno de tu otra plataforma (ej. `MACOLLO_API_KEY`). La API solo almacena el hash criptográfico SHA-256 de la clave; no es posible recuperarla si se pierde.

---

## 3. Endpoints Disponibles para Integración

| Método | Endpoint | Acceso | Descripción |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/predict` | **Requiere API Key** | Diagnóstico fitosanitario completo por imagen + temperatura. |
| `GET` | `/api/handbook` | **Requiere API Key** | Ficha técnica y medidas de Manejo Integrado de Plagas (MIP). |
| `GET` | `/api/health` | **Público** | Estado del servicio, memoria, modelo cargado y hora UTC. |
| `GET` | `/api/catalog` | **Público** | Catálogo declarativo con todos los perfiles, objetivos y estadios. |
| `GET` | `/api/profiles` | **Público** | Lista ligera de perfiles de detección activos. |

---

## 4. Parámetros del Endpoint `/api/predict`

Envía una petición `POST` con formato `multipart/form-data`:

| Parámetro | Tipo | Obligatorio | Por Defecto | Descripción |
| :--- | :---: | :---: | :---: | :--- |
| `file` | Archivo binario | **Sí** | - | Archivo de imagen (`.jpg`, `.jpeg`, `.png`, `.webp`). |
| `profile` | String | No | `"trips"` | Perfil a evaluar: `"trips"`, `"moscas"` o `"aranas_rojas"`. |
| `temperature_c` | Float | No | `20.0` | Temperatura ambiental en °C (de estaciones SIATA, Open-Meteo o sensores). |
| `crop` | String | No | `"gulupa"` | Cultivo hospedante analizado. |
| `use_tta` | Booleano | No | `false` | Activa *Test-Time Augmentation* (mayor robustez con espejo, +300ms de cómputo). |

---

## 5. Ejemplos de Conexión en Diferentes Lenguajes

### 5.1. JavaScript / TypeScript (Frontend Web: React, Vue, Svelte, Astro)

```typescript
// services/fitosanitariaService.ts
const API_URL = "https://macollo-trips-api-961314735418.us-central1.run.app";
const API_KEY = process.env.NEXT_PUBLIC_MACOLLO_API_KEY || "mk_live_tu_clave_aqui";

export interface DiagnosticoResult {
  profile: string;
  is_target: boolean;
  confidence: number;
  detected_stage?: string;
  projected_days_to_adult?: number;
  management_plan?: any;
}

export async function diagnosticarMuestra(
  imageFile: File | Blob,
  profile: "trips" | "moscas" | "aranas_rojas" = "trips",
  temperaturaC: number = 20.0
): Promise<DiagnosticoResult> {
  const formData = new FormData();
  formData.append("file", imageFile, "captura_campo.jpg");
  formData.append("profile", profile);
  formData.append("temperature_c", temperaturaC.toString());
  formData.append("crop", "gulupa");

  const response = await fetch(`${API_URL}/api/predict`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      // NOTA: NO agregar 'Content-Type'. El navegador lo define automáticamente con el boundary multipart.
    },
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Error en API Fitosanitaria (${response.status}): ${errorBody}`);
  }

  return await response.json();
}
```

---

### 5.2. Node.js / Backend (Express, NestJS, Next.js Server Actions)

```javascript
// Usando fetch nativo (Node 18+)
import fs from "node:fs";

async function consultarDiagnostico(rutaImagenLocal, temperatura = 21.5) {
  const fileBuffer = fs.readFileSync(rutaImagenLocal);
  const blob = new Blob([fileBuffer], { type: "image/jpeg" });

  const formData = new FormData();
  formData.append("file", blob, "foto.jpg");
  formData.append("profile", "trips");
  formData.append("temperature_c", String(temperatura));

  const res = await fetch("https://macollo-trips-api-961314735418.us-central1.run.app/api/predict", {
    method: "POST",
    headers: {
      "X-API-Key": process.env.MACOLLO_API_KEY,
    },
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Fallo en el servicio fitosanitario: ${res.statusText}`);
  }

  return await res.json();
}
```

---

### 5.3. Python (Microservicios, Scripts de Campo, Jupyter Notebooks)

```python
import requests

API_URL = "https://macollo-trips-api-961314735418.us-central1.run.app/api/predict"
API_KEY = "mk_live_tu_clave_aqui"

def analizar_foto(path_imagen: str, profile: str = "trips", temp_c: float = 20.5):
    headers = {
        "X-API-Key": API_KEY
    }
    
    data = {
        "profile": profile,
        "temperature_c": temp_c,
        "crop": "gulupa",
        "use_tta": "false"
    }

    with open(path_imagen, "rb") as f:
        files = {
            "file": ("foto_campo.jpg", f, "image/jpeg")
        }
        response = requests.post(API_URL, headers=headers, data=data, files=files, timeout=90)
    
    response.raise_for_status()
    resultado = response.json()
    
    print(f"Objetivo detectado: {resultado.get('target_detected')}")
    print(f"¿Es plaga objetivo?: {resultado.get('is_target')}")
    print(f"Confianza: {resultado.get('confidence') * 100:.1f}%")
    print(f"Estadio biológico: {resultado.get('detected_stage')}")
    print(f"Días restantes para adulto: {resultado.get('thermal_cycle', {}).get('projected_days_to_adult')}")
    
    return resultado

# Ejemplo de uso:
# resultado = analizar_foto("hoja_con_dano.jpg", profile="trips", temp_c=19.8)
```

---

### 5.4. Flutter / Dart (App Móvil para Agrónomos en Campo)

```dart
import 'dart:io';
import 'package:http/http.dart' as http;

Future<String> enviarMuestraFitosanitaria({
  required File imagen,
  required String apiKey,
  String profile = "trips",
  double temperatura = 20.0,
}) async {
  final uri = Uri.parse("https://macollo-trips-api-961314735418.us-central1.run.app/api/predict");
  
  final request = http.MultipartRequest("POST", uri);
  request.headers["X-API-Key"] = apiKey;
  request.fields["profile"] = profile;
  request.fields["temperature_c"] = temperatura.toString();
  request.fields["crop"] = "gulupa";

  request.files.add(await http.MultipartFile.fromPath("file", imagen.path));

  final streamedResponse = await request.send().timeout(const Duration(seconds: 90));
  final response = await http.Response.fromStream(streamedResponse);

  if (response.statusCode == 200) {
    return response.body; // JSON de predicción
  } else {
    throw Exception("Error fitosanitario (${response.statusCode}): ${response.body}");
  }
}
```

---

### 5.5. cURL (Prueba Rápida desde Terminal)

```bash
curl -X POST "https://macollo-trips-api-961314735418.us-central1.run.app/api/predict" \
     -H "X-API-Key: mk_live_tu_clave_aqui" \
     -F "file=@/ruta/a/tu/foto.jpg" \
     -F "profile=trips" \
     -F "temperature_c=22.5"
```

---

## 6. Estructura de la Respuesta JSON (`/api/predict`)

La respuesta contiene el diagnóstico biológico, agronómico y térmico unificado:

```json
{
  "profile": "trips",
  "crop": "gulupa",
  "temperature_c": 22.5,
  "is_target": true,
  "confidence": 0.892,
  "target_detected": "trips",
  "status": "confirmed",
  "margin": 0.34,
  "uncertain": false,
  "detected_stage": "larva",
  "stage_confidence": 0.865,
  "stage_description": "Larva / ninfa raspadora voraz en botón o fruto cuajado",
  "thermal_cycle": {
    "current_temperature_c": 22.5,
    "base_temperature_c": 10.0,
    "effective_degrees_day": 12.5,
    "total_cycle_gdd": 240.0,
    "projected_stage_duration_days": 6.8,
    "projected_days_to_adult": 11.2,
    "pressure_level": "alto",
    "notes": "Temperatura favorable para aceleración del ciclo reproductivo."
  },
  "agronomy_management": {
    "target_name": "Trips de las pasifloráceas (Frankliniella occidentalis)",
    "biological_control": "Liberación inoculativa de Amblyseius swirskii u Orius insidiosus. Aplicación foliar de Beauveria bassiana.",
    "ethological_control": "Instalación de trampas adhesivas cromáticas azules (~460 nm) a la altura de los brotes activos.",
    "cultural_control": "Poda fitosanitaria de brotes bajeros y frutos roñosos; retiro de arvenses hospederas.",
    "chemical_biorational": "Spinetoram o extracto concentrado de ajo/ají en focos iniciales.",
    "irac_mode_of_action": "Rotación estricta entre Grupo 5 (Spinosinas) y Grupo 4A/4D para evitar resistencia."
  },
  "gallery_match": {
    "has_match": true,
    "top_similarity": 0.784,
    "matched_stage": "larva",
    "matched_target": "trips"
  },
  "inference_time_ms": 1420.5
}
```

---

## 7. Buenas Prácticas y Rendimiento en Producción

### 7.1. Manejo del Arranque en Frío (*Cold Start*)
En Google Cloud Run, cuando la API lleva un tiempo inactiva, la cantidad de instancias baja a `0` para que el costo sea **\$0.00**.
* **Primera petición tras inactividad:** La instancia despierta y tarda entre **4 a 6 segundos**.
* **Peticiones posteriores:** Responde en **~1 a 2 segundos**.
* **Recomendación para tus clientes HTTP:** Configura un `timeout` de al menos **60 a 90 segundos** en tu cliente (Axios, Fetch, Requests, etc.) para que no corte la conexión durante el encendido de la máquina.

### 7.2. Estrategia *Keep-Alive* (Opcional)
Si deseas que la API responda siempre en menos de 1.5 segundos sin ningún cold-start:
1. Puedes crear un cron job o tarea programada gratuita (ej. cron de GitHub Actions, Cloud Scheduler o UptimeRobot) que haga un `GET /api/health` cada 10 minutos.
2. O en Cloud Run, configurar **Instancias mínimas = 1**.

### 7.3. Optimización de Imágenes en Móviles
Aunque la API ahora reduce automáticamente las fotos grandes a un tamaño óptimo (1280px), en zonas rurales con señal móvil débil (3G/HSPA) es una excelente práctica que tu app cliente comprima la foto antes de enviarla:
* Formato: **JPEG** con calidad **80% - 85%**.
* Resolución máxima recomendada: **1600 × 1200 píxeles** (un archivo de ~400 KB viaja 10 veces más rápido que un archivo de cámara original de 12 MB).

### 7.4. Política de CORS (Cross-Origin Resource Sharing)
Si tu aplicación web corre en un dominio diferente (ej. `https://mi-plataforma-agricola.com`):
* La API por defecto tiene `CORS_ORIGINS=*` habilitado para aceptar peticiones desde cualquier origen.
* Si en el futuro deseas restringirlo, puedes configurar la variable de entorno `CORS_ORIGINS` en Cloud Run separando tus dominios por comas:
  ```env
  CORS_ORIGINS=https://mi-plataforma-agricola.com,https://macollo.victormcl.me
  ```
