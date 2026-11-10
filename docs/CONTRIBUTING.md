# 🤝 Guía de Contribución — Macollo Visión Fitosanitaria API

Gracias por tu interés en colaborar con el desarrollo y optimización de la **API de Visión Fitosanitaria para Gulupa** (`macollo-trips-api`).

---

## 1. Principios de Desarrollo y Estilo de Código

1. **Python Estándar y PEP 8**: El código debe seguir rigurosamente las convenciones de estilo de PEP 8.
2. **Tipado Estático**: Utilizar anotaciones de tipo (`typing`) en todos los argumentos de funciones, métodos y retornos.
3. **Documentación Clara y en Español**: Mantener comentarios explicativos y docstrings concisos en español sobre la lógica de negocio agronómica y los endpoints.
4. **Cero Código Muerto ni Dependencias Huérfanas**: No conservar importaciones no utilizadas, variables sin uso ni funciones en desuso.
5. **No Regresiones**: Cada nueva funcionalidad o corrección debe ir acompañada de su correspondiente prueba unitaria en `backend/tests/`.

---

## 2. Configuración del Entorno de Desarrollo Local

```bash
# Clonar el repositorio
git clone https://github.com/VoctorMCL/macollo-trips-api.git
cd macollo-trips-api

# Crear y activar entorno virtual con Python 3.11 o superior
python3 -m venv .venv
source .venv/bin/activate

# Actualizar pip e instalar dependencias
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

## 3. Cómo Agregar Nuevos Objetivos o Perfiles

El conocimiento fitosanitario es declarativo y vive en
[`backend/app/domain/catalog.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/domain/catalog.py).

1. **Agregar un objetivo a un perfil existente**:
   - Registra un `DetectionTarget` con `_register(...)`.
   - Incluye su `key`, nombre común, nombre científico, `kind` (`pest`, `damage`, `healthy`, `other`) y uno o más `prompts` en inglés.
   - Añade la clave a `target_keys` del perfil correspondiente.
2. **Agregar un estadio**:
   - Crea un `StageDefinition` en el diccionario de estadios del perfil (`TRIPS_STAGES`, `MOSCAS_STAGES`, `ARANAS_ROJAS_STAGES`).
3. **Crear un perfil nuevo**:
   - Define un `DetectionProfile` con sus `target_keys`, `positive_target_keys`, `stages`, `crop`, umbrales (`min_confidence`, `min_margin`) y `agronomy_provider`.
   - Regístralo en `PROFILES`.
   - Implementa su proveedor agronómico y regístralo en [`backend/app/agronomy/registry.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/registry.py).
   - Añade pruebas en `backend/tests/test_catalog.py`.

> El motor de ML, la galería, la API y la interfaz web se adaptan automáticamente
> al catálogo. No es necesario modificar `bioclip_engine.py` para un perfil nuevo.
> Consulta la guía completa en [`docs/EXTENDING.md`](./EXTENDING.md).

---

## 4. Cómo Modificar las Recomendaciones MIP

Las directrices fitosanitarias se gestionan por proveedor agronómico:
- **Trips**: [`backend/app/agronomy/gulupa_cycle.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/gulupa_cycle.py) y [`gulupa_mip.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/gulupa_mip.py).
- **Moscas de la fruta**: [`backend/app/agronomy/flies.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/flies.py).
- **Arañas rojas**: [`backend/app/agronomy/mites.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/mites.py).
- El despacho por perfil está en [`registry.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/registry.py).

Mantén las recomendaciones organizadas en los 5 ejes obligatorios:
1. `biological_control`
2. `ethological_control`
3. `cultural_control`
4. `chemical_biorational_control` (con advertencia expresa de rotación IRAC)
5. `export_impact_alert` (alineada con requisitos de fruta fresca GlobalG.A.P.)

---

## 5. Ejecución Obligatoria de Pruebas

Antes de crear una rama o enviar un Pull Request, ejecuta la suite de pruebas automatizadas:

```bash
.venv/bin/python -m unittest discover backend/tests
```

Todas las pruebas deben finalizar en estado `OK` (actualmente **23 pruebas**).

---

## 6. Flujo de Git y Pull Requests

1. Crea una rama descriptiva a partir de `main`:
   ```bash
   git checkout -b feature/nuevo-control-biologico
   # o bien: git checkout -b fix/optimizacion-tokens
   ```
2. Realiza commits atómicos con mensajes claros en modo imperativo:
   ```bash
   git commit -m "feat(agronomy): incorporar hongo Lecanicillium en recomendaciones de ninfa"
   ```
3. Envía tu rama al repositorio remoto y abre el Pull Request hacia `main`.
