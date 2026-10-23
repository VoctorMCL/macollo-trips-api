# 🌿 Trips BioCLIP 2.5 API & Web App para Gulupa (*Passiflora edulis*)

Sistema de visión artificial y machine learning basado en **BioCLIP 2.5 (`imageomics/bioclip-2.5-vith14`)**, diseñado para el monitoreo fitosanitario y manejo agronómico de **Trips (*Thysanoptera: Thripidae*)** en invernaderos y cultivos protegidos de **Gulupa**.

---

## 🎯 Capacidades Principales

1. **Detección y Confirmación de Trips**:
   - Clasificación contrastiva frente a plagas frecuentes en pasifloráceas: Mosca Blanca (*Bemisia tabaci*), Pulgones (*Aphis gossypii*), Arañita Roja (*Tetranychus urticae*), Ácaro Plano (*Brevipalpus*) y hojas/flores sanas.
2. **Identificación del Estadio Biológico**:
   - **Adulto**: Insecto alargado, alas plumosas/franjeadas (fase de dispersión y oviposición en botones).
   - **Larva / Ninfa II**: Fase voraz de raspado (responsable directa de la "roña" o "cacarizado" en frutos tiernos).
   - **Larva / Ninfa I**: Recién eclosionada (<0.5 mm), traslúcida o blanquecina.
   - **Pupa / Prepupa**: Estadio no alimentario en reposo.
   - **Daño en Fruto / Flor**: Roña corchosa en la corteza de frutos verdes.
3. **Cálculo Térmico del Ciclo Biológico (Grados-Día)**:
   - Recibe la temperatura en tiempo real del invernadero (ej. leída desde tus APIs de **SIATA** o **Open-Meteo**).
   - Modela la duración de cada estadio y proyecta los días restantes para emergencia de adultos.
4. **Manejo Integrado de Plagas (MIP) para Gulupa de Exportación**:
   - Medidas de control biológico (*Amblyseius swirskii*, *Orius insidiosus*, *Beauveria bassiana*, *Steinernema feltiae*).
   - Control etológico con trampas adhesivas **azules** (~460 nm).
   - Control cultural y fitosanitario.
   - Control químico/biorracional con estricta pauta de rotación **IRAC** para evitar resistencia.
5. **Galería de Referencia (Few-Shot k-NN Vector Matching)**:
   - Permite colocar fotos reales de trips en `data/reference_gallery/` o subirlas desde la interfaz web.
   - Extrae vectores de 1024 dimensiones con BioCLIP 2.5 para respaldar la predicción con memoria empírica de tu predio.

---

## 📁 Estructura del Proyecto

```
/home/victormcl/Documents/Macollo/
├── backend/
│   ├── app/
│   │   ├── config.py                # Umbrales, rutas y configuración
│   │   ├── main.py                  # API FastAPI (CORS, REST, Swagger /docs)
│   │   ├── ml/
│   │   │   ├── bioclip_engine.py    # Inferencia BioCLIP 2.5, embeddings y ensamble
│   │   │   ├── taxonomy_prompts.py  # Jerarquías biológicas de trips y pasifloras
│   │   │   └── gallery_index.py     # Gestor de galería Few-Shot y similitud de cosenos
│   │   ├── agronomy/
│   │   │   ├── gulupa_cycle.py      # Modelo térmico de desarrollo (grados-día)
│   │   │   └── gulupa_mip.py        # Recomendaciones de MIP para Gulupa exportación
│   │   └── schemas/
│   │       └── prediction.py        # Modelos Pydantic de entrada/salida
│   └── tests/
│       ├── test_api.py              # Pruebas de endpoints HTTP
│       └── test_ml_pipeline.py      # Pruebas de taxonomía, ciclo y galería
├── frontend/
│   ├── index.html                   # Web App PWA móvil para agrónomos
│   ├── css/
│   │   └── style.css                # Estilos modernos de alto contraste
│   └── js/
│       ├── app.js                   # Lógica de diagnóstico y conexión con la API
│       ├── camera.js                # Control de cámara trasera y zoom macro
│       └── gallery.js               # Subida visual y reindexación de fotos
├── data/
│   └── reference_gallery/           # Tus fotos reales organizadas por estadio
│       ├── adulto/
│       ├── ninfa_1/
│       ├── ninfa_2/
│       ├── pupa/
│       └── dano_gulupa/
├── client_example.js                # Snippet JS listo para integrar en tu web actual
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
- Interfaz Web: `http://localhost:8000`
- Acceso desde celulares en el invernadero: `http://<IP-LOCAL>:8000`
- Documentación interactiva Swagger: `http://localhost:8000/docs`

---

## 🔌 Cómo Conectar tu Página Web Existente (SIATA / Open-Meteo / Sheets)

La API cuenta con **CORS habilitado (`allow_origins=["*"]`)**, por lo que puedes llamarla directamente con `fetch()` desde el código de tu web actual.

Consulta el archivo [`client_example.js`](file:///home/victormcl/Documents/Macollo/client_example.js) para el código fuente completo.

### Ejemplo de Petición en JavaScript:

```javascript
// Captura de imagen y temperatura de tu sensor/API
const formData = new FormData();
formData.append("file", imagenBlob, "muestra.jpg");
formData.append("temperature_c", "21.5"); // Temperatura actual de Open-Meteo o SIATA
formData.append("crop", "gulupa");

const res = await fetch("http://192.168.1.50:8000/api/predict", {
    method: "POST",
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
  "detected_stage": "Larva / Ninfa II (Fase de Raspado Voraz)",
  "stage_confidence": 0.887,
  "is_damage_manifestation": false,
  "cycle_info": {
    "temperature_c": 21.5,
    "detected_stage_key": "ninfa_2",
    "detected_stage_name": "Larva / Ninfa II (Fase de Raspado Voraz)",
    "current_stage_duration_days": "5.5 días a 21.5°C",
    "days_to_adult": "5.0 días (pasará a prepupa/pupa y luego a adulto)",
    "urgency_level": "CRÍTICO",
    "urgency_rationale": "La Ninfa II es el estadio con mayor consumo alimenticio..."
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

Tienes dos maneras sencillas de agregar tus fotos al modelo:

1. **Desde tu explorador de archivos**:
   Copia tus imágenes a las carpetas correspondientes en `data/reference_gallery/`:
   - `data/reference_gallery/adulto/`
   - `data/reference_gallery/ninfa_1/`
   - `data/reference_gallery/ninfa_2/`
   - `data/reference_gallery/pupa/`
   - `data/reference_gallery/dano_gulupa/`
   Luego haz clic en el botón **"Reindexar Fotos Locales"** en la Web App o llama a `POST /api/gallery/reindex`.

2. **Desde la Web App**:
   Abre la pestaña **"🖼️ Galería de Referencia"**, selecciona el estadio biológico en el menú desplegable y arrastra la foto al recuadro. BioCLIP calculará su vector inmediatamente y lo guardará en el servidor.
