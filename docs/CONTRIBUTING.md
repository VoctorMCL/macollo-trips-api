# 🤝 Guía de Contribución — Trips BioCLIP 2.5 API

Gracias por tu interés en colaborar con el desarrollo y optimización de la **API de Trips BioCLIP 2.5 para Gulupa** (`macollo-trips-api`).

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

## 3. Cómo Agregar Nuevos Prompts Taxonómicos

Si se desea incorporar una nueva plaga confusora o una nueva especie de trips:

1. Abre [`backend/app/ml/taxonomy_prompts.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/ml/taxonomy_prompts.py).
2. Si es una especie de Trips:
   - Agrega la clave al diccionario `TAXONOMIC_TARGET_PROMPTS` con su jerarquía linneana completa en inglés (Reino, Filo, Clase, Orden, Familia, Género, Especie):
     ```python
     "trips_nueva_especie": "Animalia Arthropoda Insecta Thysanoptera Thripidae NuevaEspecie, close-up photo of thrips on passionfruit..."
     ```
   - Agrega la clave a la lista `POSITIVE_TRIPS_KEYS`.
3. Si es un organismo confusor o síntoma vegetal:
   - Agrégalo como clave con prefijo `neg_` (ej. `neg_nueva_plaga`).
   - Mapea su nombre legible en el diccionario `labels_map` de [`backend/app/ml/bioclip_engine.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/ml/bioclip_engine.py).

---

## 4. Cómo Modificar las Recomendaciones MIP

Las directrices fitosanitarias se gestionan en [`backend/app/agronomy/gulupa_mip.py`](file:///home/victormcl/Documents/macollo-trips-api/backend/app/agronomy/gulupa_mip.py):
- Mantén las recomendaciones organizadas en los 5 ejes obligatorios:
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

Todas las pruebas deben finalizar en estado `OK`.

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
