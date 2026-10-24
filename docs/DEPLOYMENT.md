# 🚀 Guía de Despliegue & Operaciones — Trips BioCLIP 2.5 API

Esta guía cubre los procedimientos para poner en producción la **API de Trips BioCLIP 2.5 para Gulupa** en servidores locales de finca, máquinas virtuales en la nube (AWS EC2, GCP Compute Engine, DigitalOcean) o contenedores Docker.

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
| `SESSION_TTL_SECONDS` | Tiempo de vida de la sesión web en segundos. | `604800` (7 días) | `604800` o inferior según política de seguridad. |

---

## 3. Despliegue con Docker

El proyecto incluye un [`Dockerfile`](file:///home/victormcl/Documents/macollo-trips-api/Dockerfile) optimizado para PyTorch CPU que minimiza el tamaño de imagen.

### 3.1 Construir la Imagen
```bash
docker build -t macollo-trips-api:1.0 .
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
  macollo-trips-api:1.0
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
Description=Macollo Trips BioCLIP 2.5 API Service
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
