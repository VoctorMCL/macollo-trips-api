# 📝 Registro de Cambios (Changelog) — Trips BioCLIP 2.5 API

Todas las modificaciones notables de este proyecto se documentan en este archivo según las pautas de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y siguiendo [Versionado Semántico (SemVer)](https://semver.org/lang/es/).

---

## [1.2.0] — 2026-10-24

### ⚛️ Migración del Frontend a React + Vite
- **Reescritura Completa en React 18 + Vite**: Migración de la interfaz web desde vanilla HTML/CSS/JS hacia una arquitectura de componentes React declarativa manteniendo exactamente la misma estética visual moderna, paleta y usabilidad.
- **Hook Personalizado `useCamera`**: Gestión de streams WebRTC, selección de cámara (`environment` / `user`), recorte en canvas para zoom macro ($1.0\times$ a $4.0\times$) y congelamiento de preview.
- **Componentes Modulares**:
  - `LoginScreen`: Formulario reactivo con control de credenciales y mensajes de error del servidor.
  - `Header`: Pill con pulso de estado activo del backend y chip de usuario.
  - `NavigationTabs`: Conmutación reactiva de vistas sin recarga.
  - `ScoutView` & `DiagnosisCard`: Captura, calibración de temperatura, renderizado condicional de estadios y planes MIP.
  - `GalleryView`: Subida visual por drag & drop, selectores de fase y refresco automático de estadísticas y archivos.
  - `ApiKeysView`: Creación de claves con revelado de un solo uso, copia al portapapeles y revocación dinámica.
  - `HandbookView`: Guía técnica y daño en frutos.
  - `SpinnerOverlay`: Indicador de carga animado reutilizable.
- **Integración Transparente con FastAPI**: Compilación con Vite hacia `frontend/dist`, servido automáticamente por FastAPI en la raíz `/` con middleware de no-caché para chunks de `/assets/`.
- **Script de Arranque Automático**: `run_server.sh` ahora detecta si `frontend/dist` no ha sido compilado y ejecuta la construcción de Vite automáticamente.
- **Eliminación de Código Obsoleto**: Eliminadas carpetas anteriores `frontend/js/` y `frontend/css/`.

---

## [1.1.0] — 2026-10-24

### 🚀 Novedades y Mejoras Arquitectónicas
- **Suite Documental Oficial**: Creación de una biblioteca de documentación exhaustiva inspirada en el estándar de Macollo (`docs/README.md`, `ARCHITECTURE.md`, `ENDPOINTS.md`, `BIOCLIP-ML.md`, `AGRONOMY-MIP.md`, `AUTH.md`, `DATA-DICTIONARY.md`, `DEPLOYMENT.md`, `TESTING.md`, `TROUBLESHOOTING.md`, `SEQUENCE_DIAGRAMS.md`, `USER_MANUAL.md`, `CONTRIBUTING.md`, `CHANGELOG.md`).
- **Modularización de Esquemas**: Creación de [`backend/app/schemas/auth.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/schemas/auth.py) y centralización de importaciones en [`backend/app/schemas/__init__.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/schemas/__init__.py), eliminando declaraciones de modelos dispersas dentro de `main.py`.
- **Configuración de CORS Adaptativa**: Soporte de la variable de entorno `CORS_ORIGINS` para permitir restricción de dominios autorizados en producción sin perder compatibilidad por defecto (`*`).
- **Sanitización de Subidas**: Incorporación de sanitización de nombres de archivo mediante expresiones regulares (`re.sub`) y validación estricta de extensiones de imagen (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`) antes de persistir en `data/reference_gallery/`.
- **Aprovechamiento de Parámetro `is_damage_only`**: Enriquecimiento del módulo agronómico [`backend/app/agronomy/gulupa_mip.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/gulupa_mip.py) para que active recomendaciones especializadas de segregación de fruta con cacarizado y protección de la siguiente cohorte floral cuando solo se manifiesta daño visible.

### 🧹 Limpieza de Código y Optimización
- Eliminación de importaciones no utilizadas en `main.py` (`JSONResponse`, `FileResponse`, `GalleryItem`, `BaseModel`).
- Eliminación de importaciones muertas en `bioclip_engine.py` (`Tuple`, `settings`).
- Eliminación de importaciones muertas en `gallery_index.py` (`os`).
- Eliminación de importaciones muertas en `taxonomy_prompts.py` (`List`).

### 🧪 Aseguramiento de Calidad (Testing)
- Expansión de la suite de pruebas unitarias de 10 a **16 casos de prueba automatizados** en `backend/tests/`:
  - Pruebas de validación de extensiones y formatos de imagen.
  - Pruebas de validación de estadios inexistentes en subidas.
  - Pruebas de rechazo de archivos no-imagen en `/api/predict`.
  - Pruebas de ataque criptográfico y resistencia a manipulación de tokens de sesión (`tampered tokens`).
  - Pruebas de logout y expiración de cookies.
  - Pruebas del manejador de daños agronómicos exclusivos.

---

## [1.0.0] — 2026-10-23

### 🌟 Lanzamiento Inicial
- **Motor BioCLIP 2.5**: Integración de `imageomics/bioclip-2.5-vith14` (Vision Transformer Huge ViT-H/14) con OpenCLIP y espacio latente de 1024 dimensiones.
- **Jerarquía Taxonómica**: 14 prompts contrastivos linneanos para discriminar trips (*Frankliniella occidentalis*, *Thrips tabaci*, *Frankliniella panamensis*) frente a plagas comunes en Gulupa (*Bemisia tabaci*, *Aphis gossypii*, *Tetranychus urticae*, *Brevipalpus*, *Liriomyza*) y tejidos vegetales sanos.
- **Clasificación de 4 Fases Biológicas Reales**: Huevo, Larva (Ninfa única), Pupa/Prepupa y Adulto, más detección de Daño (Roña/Cacarizado).
- **Modelo Térmico de Grados-Día**: Cálculo de duración de estadios y proyección de días hasta la emergencia de adultos en función de la temperatura del invernadero ($T_0 = 10.5^\circ\text{C}$).
- **Memoria Empírica Few-Shot ($k$-NN)**: Indexación vectorial de fotos locales en `data/reference_gallery/` para calibrar la confianza con fotos reales de la finca.
- **Sistema de Autenticación**: Sesiones web firmadas criptográficamente con HMAC-SHA256 y API keys con prefijo `mk_` almacenadas con hash SHA-256.
- **Web App PWA Móvil**: Interfaz táctil con visor de cámara trasera, retícula de enfoque, control deslizante de Zoom Macro ($1.0\times$ a $3.0\times$) y gestión de claves.
