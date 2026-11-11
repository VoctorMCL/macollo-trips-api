# 🚀 Guía de Despliegue & Operaciones — Macollo Visión Fitosanitaria API

Esta guía cubre los procedimientos para poner en producción la **API de Visión Fitosanitaria para Gulupa** (`macollo-trips-api`) en servidores locales de finca, máquinas virtuales en la nube (AWS EC2, GCP Compute Engine, DigitalOcean) o contenedores Docker. El servicio atiende tres perfiles estables: `trips`, `moscas` (Moscas de la Fruta) y `aranas_rojas` (Arañas Rojas).

---

## 1. Requisitos de Hardware y Dimensionamiento

| Recurso | Mínimo (CPU) | Recomendado (CPU Servidor) | Óptimo (Aceleración GPU) |
| :--- | :--- | :--- | :--- |
| **Procesador** | 4 núcleos (soporte AVX2) | 8 núcleos modernos (ej. AMD EPYC / Intel Xeon) | 4 núcleos + GPU NVIDIA |
| **Memoria RAM** | 8 GB RAM | 16 GB RAM | 8 GB RAM del sistema |
| **GPU / VRAM** | No requerida | No requerida | NVIDIA RTX 3060, T4, A10 (mínimo 6 GB VRAM) |
| **Almacenamiento** | 15 GB SSD | 30 GB NVMe SSD | 30 GB NVMe SSD |
| **Tiempo de Inferencia** | ~600 - 900 ms | ~300 - 500 ms | ~60 - 120 ms |

> [!NOTE]
> BioCLIP 2.5 (`imageomics/bioclip-2.5-vith14`) descarga automáticamente aproximadamente **4.1 GB de pesos neuronales** desde HuggingFace Hub durante el primer arranque y los almacena en `~/.cache/huggingface/hub/`.

---

## 2. Variables de Entorno de Producción

| Variable | Descripción | Valor por Defecto | Recomendación en Producción |
| :--- | :--- | :---: | :--- |
| `ADMIN_USERNAME` | Usuario administrador del panel web. | `"admin"` | Definir usuario seguro corporativo. |
| `ADMIN_PASSWORD` | Contraseña maestra del panel web. | `"macollo2026"` | **Cambiar obligatoriamente** por una contraseña robusta. |
| `AUTH_SECRET_KEY` | Clave de firma simétrica HMAC-SHA256 para sesiones. | Generado en `data/.auth_secret` | Cadena aleatoria fija de al menos 64 caracteres. |
| `SESSION_COOKIE_SECURE` | Exige flag `Secure` en cookies de sesión (solo HTTPS). | `"false"` | **`"true"`** (al servir bajo HTTPS/TLS). |
| `CORS_ORIGINS` | Lista de orígenes autorizados separados por coma. | `"*"` | `https://macollo.agro.co,https://tu-app.vercel.app` |
| `DEFAULT_DETECTION_PROFILE` | Perfil usado cuando la petición no envía `profile`. | `"trips"` | `"trips"`, `"moscas"` o `"aranas_rojas"` |
| `SESSION_TTL_SECONDS` | Tiempo de vida de la sesión web en segundos. | `604800` (7 días) | `604800` o inferior según política de seguridad. |

---

## 3. Despliegue con Docker

El proyecto incluye un [`Dockerfile`](file:///home/victormcl/Documents/macollo-trips-api/Dockerfile) optimizado para PyTorch CPU que minimiza el tamaño de imagen.

### 3.1 Construir la Imagen
```bash
docker build -t macollo-trips-api:2.0 .
```

### 3.2 Ejecutar el Contenedor con Persistencia de Datos
> [!IMPORTANT]
> Es crucial montar la carpeta `./data` como volumen externo para que las fotos de la galería, las claves de API y los secretos no se pierdan al reiniciar o actualizar el contenedor.

```bash
docker run -d \
  --name trips-api \
  --restart always \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/hf_cache:/root/.cache/huggingface \
  -e ADMIN_USERNAME="admin_finca" \
  -e ADMIN_PASSWORD="ClaveMuySeguraYCompleja_2026" \
  -e SESSION_COOKIE_SECURE="true" \
  -e CORS_ORIGINS="https://macollo.agro.co" \
  macollo-trips-api:2.0
```

### 3.3 Configuración con `docker-compose.yml`
```yaml
version: '3.8'

services:
  trips-api:
    build: .
    container_name: macollo-trips-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - huggingface_cache:/root/.cache/huggingface
    environment:
      - ADMIN_USERNAME=admin_finca
      - ADMIN_PASSWORD=ClaveMuySeguraYCompleja_2026
      - SESSION_COOKIE_SECURE=true
      - CORS_ORIGINS=https://macollo.agro.co
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  huggingface_cache:
```

---

## 4. Despliegue Nativo con Systemd en Linux

Para ejecutar directamente sobre Ubuntu / Debian sin Docker:

### 4.1 Preparación del Entorno
```bash
cd /opt/macollo-trips-api
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 4.2 Crear el Servicio Systemd
Crea el archivo `/etc/systemd/system/macollo-trips.service`:

```ini
[Unit]
Description=Macollo Visión Fitosanitaria API Service
After=network.target

[Service]
Type=simple
User=victormcl
WorkingDirectory=/home/victormcl/Documents/macollo-trips-api
ExecStart=/home/victormcl/Documents/macollo-trips-api/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
Environment=ADMIN_USERNAME=admin
Environment=ADMIN_PASSWORD=macollo2026
Environment=SESSION_COOKIE_SECURE=true
Environment=CORS_ORIGINS=https://macollo.agro.co

[Install]
WantedBy=multi-user.target
```

### 4.3 Iniciar y Habilitar
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now macollo-trips.service
sudo systemctl status macollo-trips.service
```

---

## 5. Configuración de Proxy Inverso y Certificado SSL (HTTPS)

> [!CAUTION]
> Los navegadores móviles en Android y iOS (Chrome, Safari) **bloquean terminantemente el uso de la cámara WebRTC (`getUserMedia`)** cuando la conexión no viaja sobre HTTPS cifrado (la única excepción es `http://localhost`). Por ende, configurar SSL es estrictamente obligatorio para el uso de la cámara en el invernadero.

### 5.1 Configuración con Nginx y Let's Encrypt
```nginx
server {
    server_name trips.mi-finca.com;

    # Permitir subida de imágenes de alta resolución desde cámaras móviles
    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts generosos para la inferencia de Vision Transformers en CPU
        proxy_read_timeout 90s;
        proxy_connect_timeout 90s;
    }
}
```

Para generar los certificados gratuitos con Certbot:
```bash
sudo certbot --nginx -d trips.mi-finca.com
```

### 5.2 Alternativa Ligera con Caddy
Si prefieres Caddy (gestión automática de SSL):
```caddy
trips.mi-finca.com {
    request_body {
        max_size 25MB
    }
    reverse_proxy 127.0.0.1:8000
}
```

---

## 6. Exposición Temporal con Cloudflare Tunnel (Prototipo)

Si necesitas probar la API desde otra red o consumirla desde una página web externa
sin abrir puertos ni contratar un VPS, puedes publicarla temporalmente por HTTPS con
**Cloudflare Tunnel**.

```bash
# Terminal 1 — API solo accesible desde el propio equipo
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — túnel rápido gratuito
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare devuelve una URL `https://...trycloudflare.com` que se usa como base de la API.
La guía completa incluye instalación de `cloudflared`, CORS, creación de API keys,
dominio fijo con túnel nombrado, servicio systemd y solución de problemas:

➡️ **[Guía: exponer la API con Cloudflare Tunnel](./CLOUDFLARE-TUNNEL.md)**

> [!NOTE]
> El túnel rápido es solo para prototipos: la URL cambia al reiniciar y no tiene SLA.
> Para producción permanente, usa Nginx/Caddy con un dominio propio (secciones 5.1 y 5.2) o Google Cloud Run (sección 7).

---

## 7. Despliegue en Google Cloud Run (Producción Serverless Oficial)

El microservicio está optimizado para ejecutarse en **Google Cloud Run** como contenedor serverless con conexión directa a GitHub y compilación automática mediante **Cloud Build**.

### 7.1. Requisitos de Dimensionamiento en Cloud Run
El modelo **BioCLIP 2.5 (`imageomics/bioclip-2.5-vith14`)** tiene 632 millones de parámetros. Al inicializarse y realizar inferencia en CPU, alcanza un consumo pico de **~6.5 a 7.2 GB de memoria RAM**:

| Parámetro | Configuración Obligatoria | Motivo |
| :--- | :---: | :--- |
| **Memoria RAM** | **8 GiB** (o 16 GiB) | Evita la terminación por falta de memoria (OOM / Error 502 Bad Gateway). |
| **CPU asignada** | **4 vCPU** (mínimo 2 vCPU) | Reduce la inferencia a 1.2–2.0 segundos y acelera el inicio. |
| **Puerto del contenedor** | `${PORT:-8080}` | Inyectado dinámicamente por Google Cloud Run. |
| **Facturación** | *Basada en solicitudes* | Solo factura segundos activos de uso. En inactividad escala a 0 ($0.00 COP). |
| **Instancias mínimas** | `0` (ahorro) o `1` (baja latencia) | `0` para costo cero en reposo; `1` si se requiere respuesta instantánea sin cold start. |
| **Instancias máximas** | `2` o `3` | Protección estricta contra picos imprevistos de costos. |
| **Timeout de solicitud** | `120 segundos` | La API responde 503 "warming" en segundos; el margen cubre el arranque en frío. |
| **Aumento de CPU en inicio** | Habilitado (*CPU Boost*) | Acelera el arranque de la revisión. |
| **Concurrencia por instancia** | `4` (recomendado) | La inferencia serializa por un lock interno; más conexiones solo encolan peticiones. |

> [!IMPORTANT]
> **Comportamiento anti-cuelgue (cold start):** si el modelo todavía se está cargando cuando llega un `POST /api/predict`, la API espera hasta `MODEL_WAIT_SECONDS` (2.5 s por defecto) y responde **503** con cuerpo `{"status": "warming", "retry_after_seconds": N}` y cabecera `Retry-After`, en lugar de dejar la petición colgada minutos (que antes terminaba en 500/504 del proxy o del balanceador). El cliente (web de Macollo o panel React) reintenta automáticamente hasta que el modelo está listo.
>
> **Warm-up explícito:** `POST /api/warmup` (misma autenticación que `/api/predict`) dispara la carga del modelo en segundo plano y responde de inmediato con `{"model_loaded": false, "status": "loading"}`. La web de Macollo lo invoca automáticamente al abrir el escáner: para cuando el usuario encuadra y captura la foto, el modelo ya está listo y la inferencia toma ~1-2 s.

Ejemplo de despliegue con todas las banderas recomendadas:

```bash
gcloud run deploy macollo-trips-api \
  --source . \
  --region us-central1 \
  --memory 16Gi \
  --cpu 6 \
  --concurrency 4 \
  --timeout 120 \
  --min-instances 0 \
  --max-instances 3 \
  --cpu-boost \
  --allow-unauthenticated
```

> [!TIP]
> Para **latencia instantánea 24/7** (sin cold start alguno) usa `--min-instances 1`. Ten en cuenta que una instancia mínima permanente de 6 vCPU / 16 GiB factura continuamente; con `--min-instances 0` el sistema de warm-up + reintentos mantiene la primera foto del día en el rango de 30–60 s y todas las demás en ~1-3 s.

### 7.2. Características del Dockerfile para Cloud Run
1. **Multi-stage build**: La primera etapa compila la web React con Node.js 20; la segunda empaqueta FastAPI y Python 3.11.
2. **Precarga de BioCLIP 2.5**: La imagen descarga y hornea los 2.5 GB de pesos en `/root/.cache/huggingface` durante la compilación en Cloud Build.
3. **Prototipos de texto y galería precalculados**: El build ejecuta `bioclip_engine.load_model()` y guarda `data/prompt_embeddings.pt` y el índice de galería dentro de la imagen. En cada arranque en frío se cargan del disco en milisegundos en lugar de re-codificar ~100 prompts con el codificador de texto en CPU (decenas de segundos ahorradas por instancia). Si el catálogo de prompts cambia, la firma interna ya no coincide y se recalcula automáticamente.
4. **Inicio asíncrono**: `bioclip_engine.ensure_load_started()` arranca la carga en un hilo en segundo plano (`daemon=True`) para que Uvicorn abra el puerto 8080 en menos de 1 segundo y apruebe de inmediato el *startup probe* de Cloud Run.
5. **Hilos de PyTorch alineados con la cuota de CPU**: en Cloud Run el límite de CPU es una cuota CFS del cgroup; `os.cpu_count()` reporta los núcleos de la máquina anfitriona y PyTorch creaba demasiados hilos (sobre-suscripción = inferencia varias veces más lenta). Ahora el motor detecta la cuota real (`/sys/fs/cgroup/cpu.max`) y ajusta `torch.set_num_threads`. Se puede forzar con `TORCH_NUM_THREADS`.
6. **Auto-resizing de fotos**: En `backend/app/services/images.py`, las fotos capturadas con cámaras de alta resolución (12MP a 48MP) se reducen a un máximo de 1280px para prevenir saturación de memoria.

### 7.4. Integración desde la web (Vercel)

El proxy `/api/trips-diagnosis` de la web Macollo (Astro en Vercel) ahora:
1. Declara `export const maxDuration = 60` para que la función serverless no muera con 500/503 mientras Cloud Run despierta (requiere Fluid Compute: activo por defecto en Vercel).
2. Reintenta automáticamente los 503 `warming` respetando `Retry-After` durante ~50 s dentro de su presupuesto.
3. Al abrir el escáner, el health check (`GET /api/trips-diagnosis`) dispara el warm-up del modelo en Cloud Run, de modo que la primera foto suele encontrar el modelo ya listo.

Variables de entorno de la web: `ML_API_URL` (URL de Cloud Run), `ML_API_KEY`, `ML_ADMIN_USER` y `ML_ADMIN_PASSWORD` (para re-autenticación por sesión si la API key es efímera).

### 7.3. Asignación de Dominio Propio con Cloudflare
Para usar tu propio dominio (ej. `macollo.victormcl.me`):
1. En Google Cloud Run, entra al servicio `macollo-trips-api`.
2. En el menú izquierdo, haz clic en **«Asignaciones de dominios»** (*Domain mappings*) -> **«Agregar asignación»**.
3. Selecciona tu servicio y escribe tu subdominio (`macollo.victormcl.me`).
4. Google te dará un registro DNS tipo `CNAME` apuntando a `ghs.googlehosted.com`.
5. En tu panel de **Cloudflare DNS**, agrega:
   * **Tipo**: `CNAME`
   * **Nombre**: `macollo`
   * **Destino**: `ghs.googlehosted.com`
   * **Proxy status**: DNS only (Gris) o Proxied (Naranja) según tu preferencia SSL.

