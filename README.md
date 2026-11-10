# 🌿 Macollo Visión Fitosanitaria API & Web App para Gulupa (*Passiflora edulis*)

Sistema de visión artificial y machine learning basado en **BioCLIP 2.5 (`imageomics/bioclip-2.5-vith14`)** para el monitoreo fitosanitario y manejo agronómico de **Trips (*Thysanoptera: Thripidae*)**, **moscas de la fruta (*Anastrepha*)** y **arañas rojas (*Tetranychus urticae*)** en invernaderos y cultivos protegidos de **Gulupa**.

> **Compatibilidad 1.x:** el perfil `trips` y sus campos (`is_thrips`, `thrips_confidence`, `detected_stage`, carpetas `huevo`/`larva`/`pupa`/`adulto`/`dano_gulupa`) siguen funcionando igual. Los perfiles `moscas` (Moscas de la Fruta) y `aranas_rojas` (Arañas Rojas) son estables y usan el mismo motor genérico.

---

## 🎯 Capacidades Principales

1. **Catálogo fitosanitario extensible**:
   - Perfiles de detección `trips`, `moscas` y `aranas_rojas`, con objetivos, estadios y umbrales declarativos.
   - Añadir una plaga nueva solo requiere registrar datos en `backend/app/domain/catalog.py`; el motor, la API y la UI se adaptan.
   - Guía paso a paso en [`docs/EXTENDING.md`](./docs/EXTENDING.md).
2. **Detección y Confirmación de Trips**:
   - Clasificación contrastiva frente a plagas frecuentes en pasifloráceas: Mosca Blanca (*Bemisia tabaci*), Pulgones (*Aphis gossypii*), Arañita Roja (*Tetranychus urticae*), Ácaro Plano (*Brevipalpus*) y hojas/flores sanas.
3. **Identificación del Estadio Biológico** (4 fases reales del ciclo):
   - **Huevo**: Ovalado y translúcido, insertado en hojas, botones florales o frutos tiernos.
   - **Larva (Ninfa)**: Único estadio larval/ninfal, sin alas, translúcido a amarillo/anaranjado. Es la fase voraz de raspado (responsable de la "roña" o "cacarizado"). **No se divide en Ninfa I y Ninfa II.**
   - **Pupa (Prepupa)**: Estadio no alimentario en reposo, refugiado en grietas, hojarasca o suelo.
   - **Adulto**: Insecto alargado con alas plumosas/franjeadas (dispersión y oviposición).
   - **Daño en Fruto / Flor** (categoría adicional de monitoreo, no es una fase): roña corchosa en frutos verdes.
4. **Cálculo Térmico del Ciclo Biológico (Grados-Día)**:
   - Recibe la temperatura en tiempo real del invernadero (ej. leída desde tus APIs de **SIATA** o **Open-Meteo**).
   - Modela la duración de cada estadio y proyecta los días restantes para emergencia de adultos.
5. **Manejo Integrado de Plagas (MIP) para Gulupa de Exportación**:
   - Medidas de control biológico (*Amblyseius swirskii*, *Orius insidiosus*, *Beauveria bassiana*, *Steinernema feltiae*).
   - Control etológico con trampas adhesivas **azules** (~460 nm).
   - Control cultural y fitosanitario.
   - Control químico/biorracional con estricta pauta de rotación **IRAC** para evitar resistencia.
6. **Pipeline ML mejorado**:
   - Ensamble de múltiples prompts de texto por clase (prototipos más estables).
   - Votación suave de la galería few-shot y refuerzo acotado de confianza.
   - Margen de decisión, marca de incertidumbre y TTA opcional.
   - Índice de galería atómico con firma de archivos para detectar cambios.
7. **Galería de Referencia (Few-Shot k-NN Vector Matching)**:
   - Permite colocar fotos reales en `data/reference_gallery/` (trips en la raíz; perfiles nuevos en `perfil/objetivo/estadio/`) o subirlas desde la interfaz web.
   - Extrae vectores de 1024 dimensiones con BioCLIP 2.5 para respaldar la predicción con memoria empírica de tu predio.
8. **Panel privado y API keys**:
   - Login sin registro público: las credenciales del panel se definen en el servidor.
   - Sección "API y accesos" para generar y revocar claves por cliente.
   - `/api/predict` exige `X-API-Key` o una sesión web válida.

---

## 📚 Documentación Técnica y de Campo

El proyecto cuenta con una biblioteca de documentación completa e indexada en el directorio [`docs/`](./docs/README.md):

| Documento | Enfoque |
| :--- | :--- |
| [🔌 Guía de Integración para Apps Externa](./docs/INTEGRATION_GUIDE.md) | **Conectar webs (React/Next/Astro), apps móviles (Flutter) y microservicios a la API.** |
| [🏗️ Arquitectura del Sistema](./docs/ARCHITECTURE.md) | Diseño en capas, pipeline BioCLIP 2.5, k-NN Few-Shot y diagramas. |
| [🔌 Referencia de Endpoints](./docs/ENDPOINTS.md) | Catálogo completo de endpoints con bodies, headers, status y curl. |
| [🧠 Motor BioCLIP 2.5 & ML](./docs/BIOCLIP-ML.md) | Tensores 1024-d, prompts taxonómicos y formulación matemática. |
| [🧩 Extender el Catálogo](./docs/EXTENDING.md) | Cómo añadir moscas de la fruta, arañas rojas, perfiles y proveedores agronómicos. |
| [🌿 Manejo Agronómico MIP](./docs/AGRONOMY-MIP.md) | Grados-día ($T_0=10.5^\circ\text{C}$), roña en Gulupa y rotación IRAC. |
| [🔐 Autenticación & Seguridad](./docs/AUTH.md) | Sesiones HMAC-SHA256, API keys con hash SHA-256 y endurecimiento. |
| [📖 Diccionario de Datos](./docs/DATA-DICTIONARY.md) | Modelos Pydantic, respuestas JSON y esquemas en disco. |
| [🚀 Guía de Despliegue](./docs/DEPLOYMENT.md) | Docker, systemd, Nginx/Caddy con HTTPS (obligatorio para cámara WebRTC). |
| [🌐 Cloudflare Tunnel para prototipos](./docs/CLOUDFLARE-TUNNEL.md) | Publicar la API por HTTPS sin abrir puertos y consumirla desde otra página. |
| [📊 Diagramas de Secuencia](./docs/SEQUENCE_DIAGRAMS.md) | Flujos temporales en Mermaid (predicción, reindexación, login). |
| [🧪 Aseguramiento de Calidad (Testing)](./docs/TESTING.md) | Suite de 23 pruebas automatizadas, cobertura y protocolo de campo. |
| [🛠️ Resolución de Problemas](./docs/TROUBLESHOOTING.md) | Soluciones para cámara bloqueada, memoria RAM (OOM), hilos y CORS. |
| [📱 Manual de Usuario](./docs/USER_MANUAL.md) | Guía práctica para agrónomos y operarios de campo en el invernadero. |
| [🤝 Guía de Contribución](./docs/CONTRIBUTING.md) | Estándares PEP 8, typing, adición de reglas MIP y flujo Git. |
| [📝 Registro de Cambios](./docs/CHANGELOG.md) | Historial detallado de versiones y mejoras. |

---

## 📁 Estructura del Proyecto

```
/home/victormcl/Documents/macollo-trips-api/
├── backend/
│   ├── app/
│   │   ├── config.py                # Umbrales, rutas, CORS y configuración
│   │   ├── auth.py                  # Login, sesiones firmadas y API keys
│   │   ├── main.py                  # Composición FastAPI y montaje de routers
│   │   ├── domain/
│   │   │   └── catalog.py           # Catálogo extensible: perfiles, objetivos, estadios
│   │   ├── api/
│   │   │   ├── prediction_routes.py # POST /api/predict genérico por perfil
│   │   │   ├── catalog_routes.py    # Catálogo, perfiles y fichas técnicas
│   │   │   ├── gallery_routes.py    # Galería few-shot por perfil/objetivo/estadio
│   │   │   ├── auth_routes.py       # Login, logout y API keys
│   │   │   └── health_routes.py     # Estado del modelo y la galería
│   │   ├── services/
│   │   │   └── images.py            # Validación de tipo, tamaño y EXIF de subidas
│   │   ├── ml/
│   │   │   ├── bioclip_engine.py    # Motor de inferencia genérico por perfil
│   │   │   ├── prompt_bank.py       # Ensamble de prompts y prototipos de texto
│   │   │   ├── taxonomy_prompts.py  # Reexportación compatible de prompts de trips
│   │   │   └── gallery_index.py     # Índice few-shot atómico y k-NN
│   │   ├── agronomy/
│   │   │   ├── registry.py          # Despacho de proveedores agronómicos
│   │   │   ├── gulupa_cycle.py      # Modelo térmico de trips (grados-día)
│   │   │   ├── gulupa_mip.py        # Recomendaciones MIP de trips
│   │   │   ├── flies.py             # Ciclo y MIP de mosca de la fruta
│   │   │   └── mites.py             # Ciclo y MIP de araña roja
│   │   └── schemas/
│   │       ├── auth.py              # Modelos Pydantic de autenticación y API keys
│   │       └── prediction.py        # Modelos genéricos de predicción y galería
│   └── tests/
│       ├── test_api.py              # Pruebas de endpoints HTTP, seguridad y subidas
│       ├── test_catalog.py          # Pruebas del catálogo extensible y perfiles
│       └── test_ml_pipeline.py      # Pruebas de taxonomía, ciclo, MIP y criptografía
├── docs/                            # Biblioteca oficial de documentación
│   ├── README.md                    # Índice maestro de la documentación
│   ├── ARCHITECTURE.md              # Arquitectura técnica y diseño del sistema
│   ├── ENDPOINTS.md                 # Especificación de endpoints de la API
│   ├── BIOCLIP-ML.md                # Fundamentos de Machine Learning y BioCLIP
│   ├── AGRONOMY-MIP.md              # Fisiología de trips, grados-día y control MIP
│   ├── AUTH.md                      # Seguridad, sesiones firmadas y API keys
│   ├── DATA-DICTIONARY.md           # Modelos Pydantic y formatos de persistencia
│   ├── DEPLOYMENT.md                # Docker, systemd y proxy HTTPS para cámara
│   ├── CLOUDFLARE-TUNNEL.md         # Túnel HTTPS para prototipos y pruebas externas
│   ├── SEQUENCE_DIAGRAMS.md         # Diagramas de secuencia Mermaid
│   ├── EXTENDING.md                 # Guía para añadir perfiles y nuevas plagas
│   ├── TESTING.md                   # Catálogo de pruebas unitarias y de integración
│   ├── TROUBLESHOOTING.md           # Runbook para solución de incidentes
│   ├── USER_MANUAL.md               # Manual de usuario para personal de campo
│   ├── CONTRIBUTING.md               # Guía para desarrolladores y estándares
│   └── CHANGELOG.md                  # Historial de cambios y versiones
├── frontend/                        # Aplicación Web React (Vite)
│   ├── package.json                 # Dependencias React 18 & Vite 6
│   ├── vite.config.js               # Proxy hacia FastAPI (/api -> 8000)
│   ├── index.html                   # HTML base de Vite
│   ├── src/
│   │   ├── main.jsx                 # Punto de entrada React DOM
│   │   ├── App.jsx                  # Estado global, tabs, autenticación
│   │   ├── style.css                # Estilos visuales de alto contraste
│   │   ├── hooks/
│   │   │   └── useCamera.js         # Control de cámara WebRTC y zoom macro
│   │   └── components/
│   │       ├── Header.jsx           # Barra superior con status y logout
│   │       ├── LoginScreen.jsx      # Pantalla de acceso de administradores
│   │       ├── NavigationTabs.jsx   # Navegación entre vistas
│   │       ├── ScoutView.jsx        # Visor de cámara, zoom macro y diagnóstico
│   │       ├── DiagnosisCard.jsx    # Tarjeta de resultados, urgencia y MIP
│   │       ├── GalleryView.jsx      # Subida drag & drop y reindexación
│   │       ├── ApiKeysView.jsx      # Generación y revocación de API keys
│   │       ├── HandbookView.jsx     # Ficha técnica agronómica de Gulupa
│   │       └── SpinnerOverlay.jsx   # Modal de carga animado
│   └── dist/                        # Bundle optimizado compilado por Vite
├── data/
│   └── reference_gallery/           # Tus fotos reales organizadas por perfil
│       ├── huevo/                   # Trips histórico (raíz)
│       ├── larva/                   # Larva = Ninfa (una sola fase)
│       ├── pupa/
│       ├── adulto/
│       ├── dano_gulupa/
│       ├── moscas/                  # moscas/objetivo/estadio
│       └── aranas_rojas/            # aranas_rojas/objetivo/estadio
├── client_example.js                # Snippet JS listo para integrar en tu web actual
├── GUIA_CONEXION_WEB.md             # Guía paso a paso para conectar webs externas
├── requirements.txt                 # Dependencias Python
├── run_server.sh                    # Script de arranque para red local
└── README.md
```

---

## 🚀 Inicio Rápido

### 1. Activar entorno virtual e iniciar el servidor
```bash
./run_server.sh
```

El servidor quedará disponible en:
- Panel web: `http://localhost:8000`
- Acceso desde celulares en el invernadero: `http://<IP-LOCAL>:8000`
- Documentación interactiva Swagger: `http://localhost:8000/docs`

**Credenciales iniciales del panel** (cámbialas en producción con `ADMIN_USERNAME` y `ADMIN_PASSWORD`):
- Usuario: `admin`
- Contraseña: `macollo2026`

No existe registro público. Las cuentas se configuran en el servidor.

---

## 🔐 Acceso, sesiones y API keys

1. Entra al panel en `http://localhost:8000` e inicia sesión.
2. Abre la pestaña **API y accesos**.
3. Crea una clave por cliente o aplicación. La clave completa se muestra **una sola vez**.
4. La app externa debe enviar la clave en el encabezado `X-API-Key`.
5. Puedes revocar cualquier clave desde el mismo panel.

```bash
# Perfil trips (por defecto)
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: mk_tu_clave" \
  -F "file=@foto.jpg" \
  -F "temperature_c=22.5" \
  -F "crop=gulupa"

# Moscas de la fruta
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: mk_tu_clave" \
  -F "file=@foto.jpg" \
  -F "temperature_c=22.5" \
  -F "profile=moscas"

# Arañas rojas
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: mk_tu_clave" \
  -F "file=@foto.jpg" \
  -F "temperature_c=22.5" \
  -F "profile=aranas_rojas"
```

Consulta `GET /api/profiles` para ver los perfiles y objetivos disponibles, y
`GET /api/catalog` para el catálogo completo.

Variables de entorno recomendadas en producción:

```bash
export ADMIN_USERNAME="tu_usuario"
export ADMIN_PASSWORD="una_contraseña_larga_y_segura"
export AUTH_SECRET_KEY="cadena_aleatoria_larga"
export SESSION_COOKIE_SECURE="true"   # cuando sirvas el panel por HTTPS
export DEFAULT_DETECTION_PROFILE="trips"
export ENABLE_TTA="false"
```

---

## 🔌 Cómo Conectar tu Página Web Existente (SIATA / Open-Meteo / Sheets)

La API cuenta con **CORS habilitado (`allow_origins=["*"]`)**, por lo que puedes llamarla directamente con `fetch()` desde el código de tu web actual.

Consulta el archivo [`client_example.js`](file:///home/victormcl/Documents/macollo-trips-api/client_example.js) para el código fuente completo.

### Ejemplo de Petición en JavaScript:

```javascript
// Captura de imagen y temperatura de tu sensor/API
const formData = new FormData();
formData.append("file", imagenBlob, "muestra.jpg");
formData.append("temperature_c", "21.5"); // Temperatura actual de Open-Meteo o SIATA
formData.append("crop", "gulupa");

const res = await fetch("http://192.168.1.50:8000/api/predict", {
    method: "POST",
    headers: {
        "X-API-Key": "mk_tu_clave_generada_en_el_panel"
    },
    body: formData
});

const data = await res.json();
console.log(data);
```

### Formato de Respuesta JSON:

```json
{
  "is_thrips": true,
  "thrips_confidence": 0.932,
  "detected_target": "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)",
  "detected_stage": "Larva (Ninfa)",
  "stage_confidence": 0.887,
  "is_damage_manifestation": false,
  "cycle_info": {
    "temperature_c": 21.5,
    "detected_stage_key": "larva",
    "detected_stage_name": "Larva / Ninfa (Fase de Raspado)",
    "current_stage_duration_days": "9.1 días a 21.5°C",
    "days_to_adult": "5.0 días (pasará a prepupa/pupa y luego a adulto)",
    "urgency_level": "CRÍTICO",
    "urgency_rationale": "La larva (ninfa) es el estadio con mayor consumo alimenticio..."
  },
  "recommendations": {
    "biological_control": [
      "Liberación de ácaros depredadores benéficos: Amblyseius swirskii o Neoseiulus cucumeris...",
      "Introducción de chinches piratas Orius insidiosus...",
      "Aplicación de Beauveria bassiana al atardecer..."
    ],
    "ethological_control": [
      "Instalación de trampas cromotrópicas adhesivas AZULES (~460 nm)..."
    ],
    "cultural_control": [
      "Poda sanitaria en espaldera...",
      "Manejo de humedad relativa (65%-75%)..."
    ],
    "chemical_biorational_control": [
      "Jabón potásico + Azadiractina 1%...",
      "Rotación obligatoria IRAC (IRAC 5 -> IRAC 29 -> IRAC 6)..."
    ],
    "export_impact_alert": "ALERTA GULUPA EXPORTACIÓN: El raspado en frutos tiernos..."
  },
  "exemplar_matches": [],
  "inference_time_ms": 340.5
}
```

---

## 📸 Gestión de tus Fotos de Trips

> La app externa **solo envía la foto** a `POST /api/predict`. El aprendizaje/calibración con tus fotos ocurre **únicamente en esta API**, dentro de `data/reference_gallery/`. No hay que re-entrenar BioCLIP: se indexan embeddings (few-shot) y se comparan por similitud.

Tienes dos maneras sencillas de agregar tus fotos al modelo:

1. **Desde tu explorador de archivos**:
   Copia tus imágenes a las carpetas correspondientes en `data/reference_gallery/`:
   - `data/reference_gallery/huevo/`
   - `data/reference_gallery/larva/`  (larva = ninfa; una sola fase)
   - `data/reference_gallery/pupa/`
   - `data/reference_gallery/adulto/`
   - `data/reference_gallery/dano_gulupa/`
   Luego haz clic en el botón **"Reindexar Fotos Locales"** en la Web App o llama a `POST /api/gallery/reindex`.

2. **Desde la Web App**:
   Abre la pestaña **"🖼️ Galería de Referencia"**, selecciona la fase biológica en el menú desplegable y arrastra la foto al recuadro. BioCLIP calculará su vector inmediatamente y lo guardará en el servidor.

3. **Desde la API**:
   ```bash
   curl -X POST http://localhost:8000/api/gallery/upload \
     -F "file=@/ruta/a/tu_foto.jpg" \
     -F "stage=larva"
   ```
