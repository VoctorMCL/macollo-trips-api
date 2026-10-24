# 🛠️ Resolución de Problemas (Troubleshooting) — Trips BioCLIP 2.5 API

Este documento recopila diagnósticos y soluciones paso a paso para los incidentes más frecuentes durante el desarrollo, despliegue y operación en campo de **Macollo Trips API**.

---

## 🔍 Matriz de Diagnóstico Rápido

| Síntoma | Causa Más Probable | Solución Inmediata |
| :--- | :--- | :--- |
| La cámara no abre en el celular (`getUserMedia` bloqueado) | Conexión HTTP no segura. Los navegadores móviles exigen HTTPS. | Desplegar con Nginx/Caddy con certificado SSL o túnel HTTPS. |
| Error `HTTP 401 Unauthorized` al llamar desde la web externa | Clave ausente, revocada o encabezado mal escrito. | Verificar el encabezado `X-API-Key: mk_...` y su estado activo en el panel. |
| Inferencia muy lenta en CPU (> 2 segundos por foto) | Sobresuscripción de hilos o procesador sin instrucciones AVX2. | Verificar que `torch.set_num_threads` esté limitado a $\le 8$. |
| El servidor crashea al arrancar (`Killed` / OOM) | Memoria RAM insuficiente (< 6 GB) para BioCLIP ViT-H/14. | Asignar al menos 8 GB RAM, crear memoria Swap o usar fallback ViT-B/16. |
| Error de conexión al descargar pesos de Hugging Face | Bloqueo de red hacia `huggingface.co` o corte intermitente. | Descargar previamente los pesos en `~/.cache/huggingface`. |
| Las fotos copiadas a `data/reference_gallery/` no influyen | Falta reconstruir el índice de tensores en memoria. | Ejecutar `POST /api/gallery/reindex` o presionar "Reindexar" en la web. |
| Error de CORS (`blocked by CORS policy`) | Origen de la petición no contemplado en `CORS_ORIGINS`. | Configurar `export CORS_ORIGINS="*"` o agregar el dominio exacto. |

---

## 1. Problemas de Cámara y Acceso WebRTC

### Síntoma:
Al abrir la Web App desde un celular en el invernadero (`http://192.168.1.50:8000`), el cuadro de video permanece en negro o el navegador muestra el aviso *"No se pudo acceder a la cámara"*.

### Causa:
Por especificación del estándar W3C, los navegadores modernos (Google Chrome, Safari, Firefox, Edge) restringen las APIs de captura multimedia (`navigator.mediaDevices.getUserMedia`) exclusivamente a **Contextos Seguros (Secure Contexts)**:
- `http://localhost` o `http://127.0.0.1` (permitido únicamente en el propio equipo local).
- Cualquier URL remota servida mediante **HTTPS** con certificado válido.

### Solución:
1. **En Producción**: Configurar un proxy inverso con certificado SSL (ver [Guía de Despliegue](./DEPLOYMENT.md)).
2. **En Desarrollo / Pruebas de Campo Temporales**:
   - Puedes usar una herramienta de túnel seguro como [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) o `ngrok`:
     ```bash
     ngrok http 8000
     ```
   - O bien, en Chrome para Android, abrir `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, ingresar la IP local `http://192.168.1.50:8000`, habilitar y reiniciar el navegador.

---

## 2. Agotamiento de Memoria RAM (Out Of Memory - OOM)

### Síntoma:
Al ejecutar `./run_server.sh`, la consola muestra:
```text
[BioCLIPEngine] Descargando/Cargando pesos de hf-hub:imageomics/bioclip-2.5-vith14...
Killed
```

### Causa:
El Vision Transformer Huge (ViT-H/14) requiere entre 3.8 GB y 4.5 GB de memoria física durante la instanciación de pesos. En VPS o Raspberry Pi con 4 GB de RAM sin swap, el kernel Linux invoca el *OOM Killer*.

### Solución:
1. **Crear archivo de intercambio (Swap) de 4 GB**:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```
2. **Forzar el uso del modelo ligero de respaldo (ViT-B/16)**:
   Edita `backend/app/config.py` y define `BIOCLIP_MODEL_NAME = FALLBACK_MODEL_NAME`. Requiere solo ~1.2 GB de RAM.

---

## 3. Optimización de Tiempo de Inferencia en CPU

### Síntoma:
La inferencia toma más de 1.500 ms en una máquina de escritorio potente.

### Causa:
En procesadores modernos con arquitecturas híbridas (núcleos de rendimiento P-Cores y núcleos de eficiencia E-Cores), OpenMP/PyTorch puede intentar repartir el trabajo entre 24 o 32 hilos virtuales, generando una sobrecarga crítica de conmutación de contexto.

### Solución:
En `backend/app/ml/bioclip_engine.py` ya se incluye la optimización automática:
```python
if self.device.type == "cpu":
    torch.set_num_threads(min(8, torch.get_num_threads()))
```
Para afinarlo manualmente en terminal antes del arranque:
```bash
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
./run_server.sh
```

---

## 4. Fallos de Conexión con Hugging Face Hub

### Síntoma:
`requests.exceptions.ConnectionError: HTTPSConnectionPool(host='huggingface.co')` durante el arranque.

### Solución:
Si el servidor del invernadero tiene acceso a Internet restringido:
1. En una máquina con conexión, ejecuta un script para precargar el modelo en la caché local:
   ```python
   import open_clip
   open_clip.create_model_and_transforms("hf-hub:imageomics/bioclip-2.5-vith14")
   ```
2. Copia la carpeta resultante `~/.cache/huggingface/hub/` hacia el servidor de producción.
3. El motor detectará los archivos en disco y operará 100% desconectado de Internet (offline).

---

## 5. Fotos Locales de Galería No Tomadas en Cuenta

### Síntoma:
Se copiaron fotos a `data/reference_gallery/larva/`, pero el campo `exemplar_matches` en la predicción sigue saliendo vacío (`[]`).

### Causa:
Copiar archivos en disco no actualiza automáticamente la matriz de tensores en memoria.

### Solución:
Entra al panel web, abre la pestaña **Galería** y presiona el botón **"Reindexar Fotos Locales"**, o ejecuta desde terminal:
```bash
curl -X POST "http://localhost:8000/api/gallery/reindex" \
  -H "Cookie: macollo_session=<tu_cookie_de_admin>"
```
El log del servidor confirmará:
```text
[GalleryManager] Índice reconstruido con N imágenes.
```
