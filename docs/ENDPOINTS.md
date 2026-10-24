# 🔌 Referencia de Endpoints — Trips BioCLIP 2.5 API

Esta guía documenta la totalidad de los endpoints expuestos por la API REST de **Macollo Trips**, incluyendo métodos HTTP, parámetros de entrada, esquemas de respuesta, códigos de estado y ejemplos prácticos con `curl` y JavaScript `fetch`.

---

## 📋 Resumen de Endpoints

| Categoría | Método | Ruta | Autenticación | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| **Diagnóstico** | `POST` | `/api/predict` | `X-API-Key` o Sesión | Inferencia BioCLIP 2.5, estadio, ciclo térmico y MIP. |
| **Diagnóstico** | `GET` | `/api/gulupa-handbook` | `X-API-Key` o Sesión | Ficha agronómica y ciclo fenológico a temperatura dada. |
| **Salud** | `GET` | `/api/health` | Pública | Estado del servidor, modelo cargado, GPU/CPU y galería. |
| **Autenticación** | `POST` | `/api/auth/login` | Pública | Inicio de sesión administrativo en el panel web. |
| **Autenticación** | `POST` | `/api/auth/logout` | Pública | Cierre de sesión y eliminación de cookie de panel. |
| **Autenticación** | `GET` | `/api/auth/me` | Sesión requerida | Consulta del usuario actualmente autenticado. |
| **API Keys** | `GET` | `/api/keys` | Sesión requerida | Lista de claves de API activas y revocadas. |
| **API Keys** | `POST` | `/api/keys` | Sesión requerida | Emisión de una nueva API Key. Muestra la clave completa una vez. |
| **API Keys** | `DELETE` | `/api/keys/{key_id}` | Sesión requerida | Revocación inmediata de una API Key por su ID. |
| **Galería** | `GET` | `/api/gallery` | Sesión requerida | Estadísticas de fotos de referencia por estadio. |
| **Galería** | `GET` | `/api/gallery/items` | Sesión requerida | Lista detallada de archivos de fotos en disco. |
| **Galería** | `POST` | `/api/gallery/upload` | Sesión requerida | Sube una foto real y la indexa vectorialmente. |
| **Galería** | `POST` | `/api/gallery/reindex` | Sesión requerida | Fuerza el reescaneo e indexación de fotos en disco. |

---

## 1. Endpoints de Diagnóstico Fitosanitario

### 1.1 Inferencia Fitosanitaria de Trips
`POST /api/predict`

Recibe una fotografía en formato de imagen (`multipart/form-data`) junto con la temperatura actual del invernadero y devuelve el diagnóstico completo.

#### Encabezados Requeridos
| Encabezado | Valor / Ejemplo | Obligatorio |
| :--- | :--- | :--- |
| `X-API-Key` | `mk_aB3dE...` | Sí (salvo si se cuenta con cookie de sesión web) |

#### Parámetros del Formulario (`multipart/form-data`)
| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `file` | Archivo binario | Sí | Fotografía de la muestra (hoja, flor, fruto, insecto). Formatos permitidos: JPG, PNG, WebP, BMP. |
| `temperature_c` | Número flotante | No (def: `20.0`) | Temperatura ambiental en °C medida en el invernadero (ej. de SIATA u Open-Meteo). |
| `crop` | Cadena | No (def: `"gulupa"`) | Nombre del cultivo de pasiflora evaluado. |

#### Ejemplo de Petición con `curl`
```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "X-API-Key: mk_tu_clave_generada" \
  -F "file=@/home/campo/muestras/larva_flor.jpg" \
  -F "temperature_c=22.5" \
  -F "crop=gulupa"
```

#### Respuesta Exitosa (`200 OK`)
```json
{
  "is_thrips": true,
  "thrips_confidence": 0.9412,
  "detected_target": "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)",
  "detected_stage": "Larva (Ninfa)",
  "stage_confidence": 0.8954,
  "is_damage_manifestation": false,
  "cycle_info": {
    "temperature_c": 22.5,
    "detected_stage_key": "larva",
    "detected_stage_name": "Larva / Ninfa (Fase de Raspado)",
    "current_stage_duration_days": "7.9 días a 22.5°C",
    "days_to_adult": "4.6 días (pasará a pupa y luego a adulto)",
    "urgency_level": "CRÍTICO",
    "urgency_rationale": "La larva (ninfa) es el estadio con mayor consumo alimenticio. Si está presente en frutos recién cuajados (< 3 cm de diámetro), raspa la epidermis generando el 'cacarizado' o 'roña', provocando el rechazo total del fruto para exportación a Europa. Aplicar control foliar biológico o biorracional."
  },
  "recommendations": {
    "biological_control": [
      "Liberación de ácaros depredadores benéficos: Amblyseius swirskii o Neoseiulus cucumeris (dosis preventiva: 1-2 ind/m²; dosis curativa: 5-10 ind/m² en focos). Consumen vorazmente las larvas (ninfas) y los huevos de trips.",
      "Introducción de chinches piratas Orius insidiosus u Orius laevigatus (0.5 a 1 ind/m² en floración). Son los depredadores naturales más efectivos de trips adultos y ninfas dentro de las flores de Gulupa.",
      "Aplicación de hongo entomopatógeno Beauveria bassiana (cepa comercial a dosis de 1.5 - 2.0 g/L o ml/L) o Lecanicillium lecanii al atardecer (>60% HR, evitando degradación por radiación UV solar)."
    ],
    "ethological_control": [
      "Instalación de trampas cromotrópicas adhesivas AZULES (longitud de onda reflectante ~460 nm). Es el color de máxima atracción para Frankliniella occidentalis.",
      "Ubicación de trampas: Colocar en el sistema de tutorado/espaldera a la altura del estrato productivo (brotes tiernos y botones florales).",
      "Densidad recomendada: 1 trampa cada 20 m² para monitoreo continuo; 1 trampa cada 8-10 m² en bordes y focos de invernadero para trampeo masivo.",
      "Monitoreo semanal: Sacudir 20 flores y 20 brotes tiernos sobre una superficie blanca para conteo directo. Umbral de acción: > 1-2 trips/flor en época de cuaje."
    ],
    "cultural_control": [
      "Poda sanitaria y aclareo de zarcillos secos y hojas senescentes en la espaldera para mejorar ventilación y penetración de aspersiones fitosanitarias.",
      "Erradicación estricta de malezas reservorio hospederas en calles y perímetro del lote (Cerraja: Sonchus oleraceus; Chipaca: Bidens pilosa; Malva spp.).",
      "Manejo de humedad relativa: Mantener la HR entre 65% y 75% en el invernadero mediante nebulización o ventilación. Ambientes secos (HR < 50%) aceleran exponencialmente la reproducción de trips.",
      "Mallas anti-insectos (mínimo 50 mesh / 10x20 hilos por cm²) en ventanas laterales y cenitales del invernadero con doble puerta de acceso."
    ],
    "chemical_biorational_control": [
      "Biorracional de contacto: Jabón potásico (3-5 cc/L) en mezcla con extracto de Neem (Azadiractina 1%, 1.5 cc/L). Bloquea la muda de ninfas y actúa como repelente anti-alimentario.",
      "Aceites esenciales agrícolas: Extracto de canela o aceite de naranja para degradar la cutícula del insecto y deshidratarlo sin generar resistencia.",
      "Grupo IRAC 5 (Espinocinas): Spinosad (0.2 - 0.4 cc/L) o Spinetoram. Excelente eficacia por ingestión y contacto en adultos y ninfas. Usar máximo 2 aplicaciones seguidas por ciclo.",
      "Grupo IRAC 29 (Bloqueadores de alimentación): Flonicamid (0.15 - 0.2 g/L). Detiene la alimentación por estilete en menos de 1 hora, preservando fauna benéfica.",
      "Grupo IRAC 6 (Avermectinas): Abamectina (0.5 - 0.75 cc/L) en mezcla con aceite mineral parafínico coadyuvante (0.25%).",
      "ADVERTENCIA DE ROTACIÓN: Los trips desarrollan resistencia a insecticidas con extrema rapidez. Es obligatorio rotar entre diferentes grupos IRAC (ej. IRAC 5 -> IRAC 29 -> IRAC 6) en cada ventana de aplicación."
    ],
    "export_impact_alert": "ALERTA GULUPA EXPORTACIÓN: El raspado de trips en flores recién fecundadas y frutitos en cuaje (menores a 3 cm) induce cicatrización hipertrófica peridérmica ('roña' o 'cacarizado'). Frutos con más de 1 cm² de lesión son descartados automáticamente de cajas de exportación tipo Europa (GlobalG.A.P.). Intervenir preventivamente en pre-floración y caída de pétalos."
  },
  "exemplar_matches": [],
  "diagnostics": {
    "model_used": "hf-hub:imageomics/bioclip-2.5-vith14",
    "device": "cpu",
    "top_target_prompt_key": "trips_frankliniella_occidentalis",
    "positive_zero_shot_prob": 0.9412,
    "gallery_boost_applied": 0.0,
    "temperature_input_c": 22.5
  },
  "inference_time_ms": 328.45
}
```

#### Códigos de Error Posibles
- `400 Bad Request`: El archivo no es una imagen válida o está dañado.
- `401 Unauthorized`: No se envió `X-API-Key` o la clave está revocada/inactiva.
- `500 Internal Server Error`: Fallo interno durante la inferencia en PyTorch.

---

### 1.2 Manual Agronómico y Ciclo a Temperatura Dada
`GET /api/gulupa-handbook`

Retorna la ficha técnica de plagas y el ciclo biológico modelado para una temperatura específica.

#### Parámetros de Consulta (Query String)
| Parámetro | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `temperature_c` | Número flotante | No (def: `20.0`) | Temperatura a evaluar (°C). |

#### Ejemplo con `curl`
```bash
curl -X GET "http://localhost:8000/api/gulupa-handbook?temperature_c=24.0" \
  -H "X-API-Key: mk_tu_clave"
```

---

## 2. Endpoints de Salud y Estado

### 2.1 Verificación de Salud
`GET /api/health`

Endpoint liviano y público (sin autenticación) para balanceadores de carga, scripts de monitorización o pings periódicos.

#### Ejemplo de Respuesta
```json
{
  "status": "healthy",
  "app_name": "Gulupa Trips BioCLIP 2.5 API",
  "version": "1.0.0",
  "model_loaded": true,
  "model_name": "hf-hub:imageomics/bioclip-2.5-vith14",
  "device": "cpu",
  "gallery_total_images": 12,
  "gallery_is_indexed": true,
  "server_time_iso": "2026-10-24T10:00:00Z"
}
```

---

## 3. Endpoints de Autenticación del Panel

### 3.1 Inicio de Sesión
`POST /api/auth/login`

Valida las credenciales del administrador y emite una cookie segura `macollo_session`.

#### Cuerpo de la Petición (`application/json`)
```json
{
  "username": "admin",
  "password": "tu_password_configurado"
}
```

#### Respuesta (`200 OK`)
```json
{
  "authenticated": true,
  "username": "admin"
}
```
*Encabezado de respuesta:* `Set-Cookie: macollo_session=<token>; HttpOnly; SameSite=Lax; Max-Age=604800`

### 3.2 Cierre de Sesión
`POST /api/auth/logout`

Elimina la cookie de sesión del navegador.

### 3.3 Verificación de Sesión Actual
`GET /api/auth/me`

Devuelve el nombre del usuario si la cookie de sesión es válida. Retorna `401 Unauthorized` si ha expirado.

---

## 4. Endpoints de Gestión de API Keys

> Todos los endpoints de API Keys requieren una sesión de administrador activa (`require_session`).

### 4.1 Listar Claves Registradas
`GET /api/keys`

Devuelve todas las claves creadas con sus metadatos (el token secreto completo nunca se vuelve a exponer).

```json
{
  "items": [
    {
      "id": "e4a2bc1f90123456",
      "name": "Servidor Web Macollo Vercel",
      "key_prefix": "mk_A9xL7p2q…",
      "created_at": "2026-10-23T18:00:00Z",
      "created_by": "admin",
      "last_used_at": "2026-10-24T09:45:10Z",
      "active": true
    }
  ]
}
```

### 4.2 Crear Nueva API Key
`POST /api/keys`

#### Cuerpo de la Petición (`application/json`)
```json
{
  "name": "Aplicación Móvil Finca La Esperanza"
}
```

#### Respuesta (`200 OK`)
```json
{
  "message": "API key creada. Guárdala ahora: no se volverá a mostrar.",
  "raw_key": "mk_1A2b3C4d5E6f7G8h9I0jK1L2m3N4o5P6q7R8s9T0u1V2w3X4y5Z",
  "key": {
    "id": "f89a12c45e678901",
    "name": "Aplicación Móvil Finca La Esperanza",
    "key_prefix": "mk_1A2b3C4d5",
    "created_at": "2026-10-24T10:05:00Z",
    "created_by": "admin",
    "last_used_at": null,
    "active": true
  }
}
```

### 4.3 Revocar API Key
`DELETE /api/keys/{key_id}`

Invalida inmediatamente la clave especificada. Retorna `404 Not Found` si el identificador no existe.

---

## 5. Endpoints de la Galería de Referencia (Few-Shot)

### 5.1 Estadísticas de la Galería
`GET /api/gallery`

```json
{
  "total_images": 24,
  "by_stage": {
    "huevo": 4,
    "larva": 10,
    "pupa": 3,
    "adulto": 5,
    "dano_gulupa": 2
  },
  "is_indexed": true,
  "index_path": "/home/.../data/gallery_embeddings.pt"
}
```

### 5.2 Subir Foto Real a la Galería
`POST /api/gallery/upload`

Permite guardar una nueva imagen en el banco de fotos de la finca y recalcular automáticamente el índice de tensores.

#### Parámetros (`multipart/form-data`)
| Campo | Tipo | Requerido | Valores Permitidos |
| :--- | :--- | :--- | :--- |
| `file` | Binario | Sí | Imagen JPG, PNG, WebP |
| `stage` | Texto | Sí | `huevo`, `larva`, `pupa`, `adulto`, `dano_gulupa` |

### 5.3 Forzar Reindexación Local
`POST /api/gallery/reindex`

Recorre todos los archivos colocados manualmente en `data/reference_gallery/`, genera sus vectores latentes con BioCLIP 2.5 y actualiza `gallery_embeddings.pt`.
