# Guía paso a paso: probar la API en local y conectarla a tu web

Esta guía cubre dos cosas en el mismo lugar:

1. **Probar la API en local** (que responda y que el modelo detecte).
2. **Conectarla a tu sitio web** (Astro en producción) y dejarla funcionando.

La API 2.x atiende tres perfiles fitosanitarios estables: **`trips`** (trips),
**`moscas`** (moscas de la fruta) y **`aranas_rojas`** (araña roja). El perfil se
envía en cada predicción y determina las clases y el plan MIP que recibes.

> No necesitas `frontend/index.html` ni `frontend/css/`. Eso es solo una demo.
> Tu web Astro consume la API por HTTP; la API no necesita saber cómo está hecha tu web.

Ruta del proyecto en este equipo:

```text
/home/victormcl/Documents/macollo-trips-api
```

---

## 0. Cómo funciona la conexión (modelo mental)

```text
Navegador del usuario
        │
        │  POST /api/predict  (foto + temperatura + perfil)
        ▼
Tu web Astro  ──────────────►  API FastAPI + BioCLIP 2.5
   (HTML/JS)                        (Python, puerto 8000)
                                        │
                                        ▼
                                   Respuesta JSON
                    (profile, detection, estadio, ciclo, MIP)
```

La foto **sale del navegador** y se envía a la API. La API responde un JSON.
Tu web solo muestra ese JSON (o guarda los datos en tu Google Sheet, base de datos, etc.).

Hay dos formas de exponer la API:

- **Desarrollo/local:** `http://localhost:8000` o `http://IP-DE-TU-PC:8000`.
- **Producción:** `https://api.tudominio.com` (con HTTPS). Nunca publiques el puerto `8000` directo a internet.

---

# PARTE 1 — Probarla en local

## 1.1. Abrir la terminal en el proyecto

```bash
cd /home/victormcl/Documents/macollo-trips-api
```

## 1.2. Activar el entorno virtual

```bash
source .venv/bin/activate
```

Debes ver que el prompt cambia (aparece `(.venv)` al inicio). Verifica Python y dependencias:

```bash
python -c "import fastapi, torch, open_clip; print('dependencias OK')"
```

Si falla, instala de nuevo:

```bash
pip install -r requirements.txt
```

## 1.3. Iniciar el servidor

Para desarrollo (se reinicia solo cuando cambias código):

```bash
./run_server.sh
```

O manualmente, sin autorecarga:

```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Qué verás en la terminal:

```text
[Macollo Visión Fitosanitaria API] Iniciando servicio...
[BioCLIPEngine] Inicializando en dispositivo: cpu
[BioCLIPEngine] Descargando/Cargando pesos de hf-hub:imageomics/bioclip-2.5-vith14...
[BioCLIPEngine] Precalculando embeddings de texto por perfil (trips, moscas, aranas_rojas)...
[BioCLIPEngine] Modelo hf-hub:imageomics/bioclip-2.5-vith14 cargado y listo.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**La primera vez tarda varios minutos** porque descarga ~4 GB de pesos del modelo desde Hugging Face.
En este equipo ya están descargados en `~/.cache/huggingface`, así que tarda 1–2 minutos en cargar.
Deja esa terminal abierta: ahí corre el servidor.

## 1.4. Verificar que está viva

Abre otra terminal y ejecuta:

```bash
curl http://localhost:8000/api/health
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "app_name": "Macollo Visión Fitosanitaria API",
  "version": "2.0.0",
  "model_loaded": true,
  "model_name": "hf-hub:imageomics/bioclip-2.5-vith14",
  "device": "cpu",
  "default_profile": "trips",
  "profiles": [
    {"key": "trips", "name": "Trips", "experimental": false},
    {"key": "moscas", "name": "Moscas de la Fruta", "experimental": false},
    {"key": "aranas_rojas", "name": "Arañas Rojas", "experimental": false}
  ],
  "gallery_total_images": 0,
  "gallery_is_indexed": false,
  "gallery_is_stale": false,
  "server_time_iso": "2026-11-10T10:00:00Z"
}
```

Lo importante es `"model_loaded": true`. Si está en `false`, espera un poco: el modelo todavía está cargando.

También puedes abrir en el navegador:

- Panel web con login: <http://localhost:8000>
- Documentación interactiva (Swagger): <http://localhost:8000/docs>
- Estado: <http://localhost:8000/api/health>

Credenciales iniciales del panel: usuario `admin` y contraseña `macollo2026`.
Cámbialas en producción con las variables de entorno `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
No hay registro público.

## 1.5. Crear una API key y probar una predicción

La API de predicción ya no es pública. Primero inicia sesión en el panel
(`http://localhost:8000`) y crea una clave en **API y accesos**.

También puedes hacerlo por terminal, guardando la cookie de sesión:

```bash
# 1) Login del panel (guarda la cookie en cookies.txt)
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"macollo2026"}'

# 2) Crear una API key (la respuesta trae raw_key)
curl -b cookies.txt -X POST http://localhost:8000/api/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"Mi aplicacion"}'
```

Copia el valor de `raw_key` y úsalo en la predicción:

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: mk_tu_clave" \
  -F "file=@/ruta/a/tu/foto.jpg" \
  -F "temperature_c=22.5" \
  -F "crop=gulupa" \
  -F "profile=trips"
```

Cambia `/ruta/a/tu/foto.jpg` por la ruta real. Si el archivo está en el escritorio:

```bash
-F "file=@/home/victormcl/Escritorio/foto.jpg"
```

Respuesta (resumida):

```json
{
  "profile": "trips",
  "crop": "gulupa",
  "is_thrips": true,
  "thrips_confidence": 0.87,
  "detected_target": "Trips de las Flores (Frankliniella occidentalis / Thrips tabaci)",
  "detected_stage": "Prepupa / Pupa",
  "stage_confidence": 0.89,
  "is_damage_manifestation": false,
  "detection": {
    "profile": "trips",
    "profile_name": "Trips",
    "category": "pest",
    "is_positive": true,
    "confidence": 0.87,
    "is_uncertain": false,
    "target_key": "trips_frankliniella_occidentalis",
    "target_name": "Trips de las Flores",
    "scientific_name": "Frankliniella occidentalis",
    "profile_experimental": false,
    "scores": {
      "trips_frankliniella_occidentalis": 0.62,
      "trips_general": 0.21,
      "neg_mosca_blanca": 0.05
    }
  },
  "cycle_info": {
    "temperature_c": 22.5,
    "current_stage_duration_days": "4.6 días a 22.5°C",
    "days_to_adult": "2.7 días para emergencia masiva de adultos",
    "urgency_level": "ALTO"
  },
  "recommendations": {
    "biological_control": ["..."],
    "ethological_control": ["..."],
    "cultural_control": ["..."],
    "chemical_biorational_control": ["..."],
    "export_impact_alert": "..."
  },
  "exemplar_matches": [],
  "inference_time_ms": 2360.5
}
```

Notas:

- `temperature_c` es opcional; si no lo envías, usa `20.0`.
- `crop` es opcional y por ahora es informativo (`gulupa` por defecto).
- `profile` es opcional; si no lo envías, usa `trips`. Valores: `trips`, `moscas` o `aranas_rojas`.
- `detection` es el contrato genérico 2.x: úsalo en código nuevo (`is_positive`, `category`, `confidence`, `target_key`, `scores`). Los campos `is_thrips` y `thrips_confidence` se conservan solo por compatibilidad con la versión 1.x.
- `exemplar_matches` estará vacío hasta que agregues fotos a la galería del perfil (ver 1.7).

## 1.6. Probar desde Swagger (sin terminal)

1. Abre <http://localhost:8000/docs>.
2. Despliega `POST /api/predict`.
3. Clic en **Try it out**.
4. En `file`, clic en **Choose File** y selecciona una foto.
5. En `temperature_c` escribe, por ejemplo, `22.5`.
6. En `profile` escribe `trips`, `moscas` o `aranas_rojas` según la plaga que estés monitoreando.
7. Si vas a usar `X-API-Key`, primero inicia sesión en el panel o pulsa **Authorize** con tu clave.
8. Clic en **Execute**.
9. Revisa el **Response body** y el código `200`.

Si responde `200`, la API está funcionando de punta a punta.

## 1.7. Agregar tus fotos reales (mejora la detección)

La API compara la foto nueva contra tus fotos de referencia (búsqueda de similitud).
Al principio la galería está vacía. La app externa solo envía la foto: el "entrenamiento"
(few-shot) se hace aquí, indexando las fotos de `data/reference_gallery/`.

Las fotos se buscan **dentro del mismo perfil**: una foto de `moscas` no se usa
para calibrar `trips`, ni al revés.

**Opción A — desde el sistema de archivos:**

```bash
# Trips conserva las carpetas históricas en la raíz
cp /ruta/mi_foto_adulto.jpg data/reference_gallery/adulto/
cp /ruta/mi_foto_larva.jpg  data/reference_gallery/larva/

# Perfiles nuevos: perfil/objetivo/estadio
cp /ruta/mi_foto_mosca.jpg \
  data/reference_gallery/moscas/mosca_frutal_anastrepha/adulto/
cp /ruta/mi_foto_arania.jpg \
  data/reference_gallery/aranas_rojas/arana_roja_tetranychus/adulto/
```

Carpetas válidas de trips:

```text
data/reference_gallery/huevo/
data/reference_gallery/larva/      # Larva = Ninfa (una sola fase)
data/reference_gallery/pupa/
data/reference_gallery/adulto/
data/reference_gallery/dano_gulupa/
```

La lista exacta y vigente de todas las carpetas se obtiene con:

```bash
curl -b cookies.txt "http://localhost:8000/api/gallery/labels"
curl -b cookies.txt "http://localhost:8000/api/gallery/labels?profile=moscas"
```

Luego reindexa:

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/gallery/reindex
```

**Opción B — subir por la API:**

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/gallery/upload \
  -F "file=@/ruta/a/tu/foto.jpg" \
  -F "label=moscas/mosca_frutal_anastrepha/adulto"
```

`label` es la clave exacta que devuelve `/api/gallery/labels` (la más segura).
También puedes usar `profile` + `target` + `stage`; por ejemplo
`profile=trips&stage=larva` o
`profile=aranas_rojas&target=arana_roja_tetranychus&stage=dano`.

Ver el estado de la galería (con desglose por perfil, objetivo y estadio):

```bash
curl -b cookies.txt http://localhost:8000/api/gallery
curl -b cookies.txt http://localhost:8000/api/gallery/items
```

## 1.8. Probar desde el celular en la misma red Wi-Fi

El servidor escucha en `0.0.0.0`, así que es accesible desde la red local.

1. Averigua la IP de tu PC:

   ```bash
   hostname -I
   ```

   Ejemplo: `192.168.1.50`.

2. Desde el celular (misma Wi-Fi) abre:

   ```text
   http://192.168.1.50:8000/docs
   ```

3. Si no carga, permite el puerto solo en la red local:

   ```bash
   sudo ufw allow 8000/tcp
   ```

   No abras el puerto `8000` en el router hacia internet. Para producción usa HTTPS y un proxy (Parte 3).

4. Prueba una foto desde el celular en Swagger. La cámara trasera suele funcionar mejor con buena luz y acercamiento.

## 1.9. Ejecutar las pruebas automáticas

Con el servidor detenido o en otra terminal:

```bash
cd /home/victormcl/Documents/macollo-trips-api
source .venv/bin/activate
python -m unittest discover -s backend/tests -v
```

Debes ver:

```text
Ran 23 tests in ...
OK
```

## 1.10. Detener el servidor

En la terminal donde corre uvicorn: `Ctrl + C`.

Si quedó en segundo plano:

```bash
pkill -f "uvicorn backend.app.main"
```

---

# PARTE 2 — Conectarla a tu web (Astro)

## 2.1. Decidir la URL de la API

| Entorno | URL de la API |
|---|---|
| Desarrollo local | `http://localhost:8000` |
| Celular en la misma Wi-Fi | `http://192.168.1.50:8000` |
| Producción | `https://api.tudominio.com` |

En producción, si tu web Astro está en **HTTPS**, la API **también debe ser HTTPS**. Si no, el navegador bloquea la petición por `mixed content`.

## 2.2. Crear las variables de entorno en Astro

En la raíz de tu proyecto Astro crea o edita `.env`:

```env
PUBLIC_API_URL=http://localhost:8000
```

Reglas:

- El prefijo `PUBLIC_` es obligatorio para que Astro la exponga al navegador.
- Sin `/` al final.
- `localhost` solo funciona en tu PC. Desde el celular usa la IP de tu PC.
- Después de cambiar `.env`, reinicia `npm run dev` (o vuelve a hacer el build).

En producción, en el servidor o en el panel de tu hosting (Vercel, Netlify, etc.):

```env
PUBLIC_API_URL=https://api.tudominio.com
PUBLIC_API_KEY=mk_tu_clave_generada_en_el_panel
```

Recuerda que Astro inyecta las variables `PUBLIC_*` **en tiempo de build**. Debes volver a construir y desplegar después de cambiarla.

> [!WARNING]
> Cualquier variable `PUBLIC_*` queda visible en el JavaScript del navegador. Para
> un sitio público, no expongas una API key maestra: usa una clave dedicada y
> restringida, o llama a la API desde un endpoint SSR de Astro (sección 3.9) para
> que la clave viva solo en el servidor.

## 2.3. Crear el componente de diagnóstico

Crea un archivo, por ejemplo `src/components/DiagnosticoFitosanitario.astro`:

```astro
---
// src/components/DiagnosticoFitosanitario.astro
---
<div>
  <h2>Diagnóstico fitosanitario en gulupa</h2>

  <label for="perfil">Perfil</label>
  <select id="perfil">
    <option value="trips">Trips</option>
    <option value="moscas">Moscas de la Fruta</option>
    <option value="aranas_rojas">Arañas Rojas</option>
  </select>

  <input id="foto" type="file" accept="image/*" capture="environment" />
  <button id="analizar" type="button">Analizar foto</button>

  <p id="estado"></p>
  <pre id="resultado" style="white-space: pre-wrap;"></pre>
</div>

<script>
  const API =
    import.meta.env.PUBLIC_API_URL ||
    (import.meta.env.DEV ? "http://localhost:8000" : "");
  const API_KEY = import.meta.env.PUBLIC_API_KEY || "";

  const input = document.getElementById("foto");
  const perfil = document.getElementById("perfil");
  const boton = document.getElementById("analizar");
  const estado = document.getElementById("estado");
  const salida = document.getElementById("resultado");

  boton?.addEventListener("click", async () => {
    if (!API) {
      estado.textContent = "Falta PUBLIC_API_URL en el build de producción.";
      return;
    }

    const archivo = input?.files?.[0];

    if (!archivo) {
      estado.textContent = "Selecciona una foto primero.";
      return;
    }

    const form = new FormData();
    form.append("file", archivo, "muestra.jpg");
    form.append("temperature_c", "22.5"); // cámbialo por el dato real
    form.append("crop", "gulupa");
    form.append("profile", perfil?.value || "trips");

    estado.textContent = "Analizando con BioCLIP...";
    salida.textContent = "";

    try {
      const res = await fetch(`${API}/api/predict`, {
        method: "POST",
        headers: API_KEY ? { "X-API-Key": API_KEY } : {},
        body: form,
        // No agregues "Content-Type": el navegador pone el boundary solo.
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }

      const data = await res.json();
      const det = data.detection ?? {};

      estado.textContent = det.is_positive
        ? `${det.target_name} — ${data.detected_stage} (urgencia: ${data.cycle_info?.urgency_level ?? "N/A"})`
        : `Sin detección positiva — ${data.detected_target}`;

      salida.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      estado.textContent = "Error: " + error.message;
      console.error(error);
    }
  });
</script>
```

## 2.4. Usarlo en una página

En cualquier página `.astro`:

```astro
---
import DiagnosticoFitosanitario from "../components/DiagnosticoFitosanitario.astro";
---

<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Diagnóstico fitosanitario</title>
  </head>
  <body>
    <main>
      <DiagnosticoFitosanitario />
    </main>
  </body>
</html>
```

Si ya tienes tu layout y tu diseño, solo importa y usa `<DiagnosticoFitosanitario />` dentro de tu página existente. No necesitas tocar tus estilos.

## 2.5. Probar la conexión en desarrollo

1. Terminal 1 — API:

   ```bash
   cd /home/victormcl/Documents/macollo-trips-api
   source .venv/bin/activate
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

2. Terminal 2 — tu Astro:

   ```bash
   cd /ruta/a/tu-proyecto-astro
   npm install      # solo la primera vez
   npm run dev
   ```

3. Abre la URL que muestra Astro (normalmente `http://localhost:4321`).
4. Entra a la página del componente, selecciona una foto y pulsa **Analizar foto**.
5. Abre la consola del navegador (F12) si algo falla.

Si ves `Error: Failed to fetch`:

- ¿Está corriendo uvicorn en el puerto 8000?
- ¿La URL en `.env` es correcta y reiniciaste el dev server?
- ¿Estás abriendo la web desde el celular con `localhost`? Debe ser la IP de tu PC.

## 2.6. Obtener la temperatura automáticamente (opcional)

La API acepta la temperatura del invernadero. Si ya usas SIATA u Open-Meteo, puedes enviarla así:

```js
async function temperaturaActual(lat, lon) {
  const url =
    `https://api.open-meteo.com/v1/forecast` +
    `?latitude=${lat}&longitude=${lon}&current=temperature_2m`;
  const res = await fetch(url);
  const json = await res.json();
  return json.current.temperature_2m;
}

// Uso:
const temp = await temperaturaActual(4.711, -74.0721); // Bogotá, ajusta a tu lote
form.append("temperature_c", String(temp));
```

Si no envías `temperature_c`, la API usa `20.0 °C`.

## 2.7. Mostrar solo lo importante en tu web

El JSON trae mucha información técnica. Para una tarjeta simple:

```js
const det = data.detection ?? {};

const resumen = {
  perfil: data.profile,
  esObjetivoPositivo: det.is_positive ?? data.is_thrips,
  confianza: `${((det.confidence ?? data.thrips_confidence ?? 0) * 100).toFixed(1)}%`,
  categoria: det.category,
  estadio: data.detected_stage,
  objetivo: data.detected_target,
  urgencia: data.cycle_info?.urgency_level ?? "N/A",
  diasParaAdulto: data.cycle_info?.days_to_adult ?? "N/A",
  primeraAccion: data.recommendations?.biological_control?.[0] ?? "Monitoreo preventivo",
  alertaExportacion: data.recommendations?.export_impact_alert ?? "",
};
```

---

# PARTE 3 — Ponerla en producción

## 3.1. Dónde debe correr la API

La API es un servidor Python con un modelo de ~4 GB en RAM. No corre en un hosting estático ni en Netlify/Vercel Functions.

Necesitas una máquina o VPS con:

- Linux (Ubuntu/Debian recomendado)
- Al menos **8 GB de RAM** (ideal 12–16 GB)
- Python 3.10+
- Puertos 80/443 abiertos
- El puerto 8000 **cerrado** al público

Si tu Astro está en Netlify/Vercel pero la API en un VPS, igual funciona: la web llama por HTTPS a `https://api.tudominio.com`.

## 3.2. Copiar el proyecto al servidor

```bash
rsync -av --exclude '.venv' --exclude '__pycache__' \
  /home/victormcl/Documents/macollo-trips-api/ usuario@servidor:/opt/macollo/
```

Esto incluye tus fotos de `data/reference_gallery/` si ya las tienes.

En el servidor:

```bash
cd /opt/macollo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

La primera ejecución descarga el modelo (~4 GB). Puedes autenticarte para mayor velocidad:

```bash
export HF_TOKEN="hf_tu_token"
```

## 3.3. Probar en el servidor (antes del proxy)

```bash
cd /opt/macollo
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal del servidor:

```bash
curl http://127.0.0.1:8000/api/health
```

Debe decir `"model_loaded": true`.

> `--host 127.0.0.1` significa que solo el propio servidor puede acceder. El proxy (Caddy/Nginx) será el que reciba internet.

## 3.4. Crear el servicio systemd (que arranque solo)

Crea `/etc/systemd/system/macollo-api.service`:

```ini
[Unit]
Description=Macollo Visión Fitosanitaria API
After=network-online.target
Wants=network-online.target

[Service]
User=victormcl
WorkingDirectory=/opt/macollo
ExecStart=/opt/macollo/.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> Ajusta `User`, `WorkingDirectory` y `ExecStart` si tu proyecto está en otra ruta.
> El usuario del servicio debe tener permisos de escritura en `data/`.
> El modelo se guarda en `~/.cache/huggingface` del usuario del servicio. Si ya lo
> descargaste manualmente con ese mismo usuario, no se vuelve a descargar.
> Usa **un solo worker**: cada worker cargaría el modelo y consumiría ~4 GB extra.

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now macollo-api
sudo systemctl status macollo-api
```

Ver logs:

```bash
journalctl -u macollo-api -f
```

## 3.5. HTTPS con Caddy (recomendado)

Caddy gestiona el certificado SSL automáticamente.

1. En tu DNS, crea un registro tipo `A` para `api.tudominio.com` apuntando a la IP del servidor.
2. Instala Caddy:

   ```bash
   sudo apt install caddy
   ```

3. Edita `/etc/caddy/Caddyfile`:

   ```caddyfile
   api.tudominio.com {
       reverse_proxy 127.0.0.1:8000

       request_body {
           max_size 20MB
       }
   }
   ```

4. Recarga:

   ```bash
   sudo systemctl reload caddy
   ```

5. Verifica:

   ```bash
   curl https://api.tudominio.com/api/health
   ```

## 3.6. Alternativa con Nginx

```nginx
server {
    listen 443 ssl;
    server_name api.tudominio.com;

    ssl_certificate     /etc/letsencrypt/live/api.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tudominio.com/privkey.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 180s;
    }
}
```

Certificado con Certbot:

```bash
sudo certbot --nginx -d api.tudominio.com
```

## 3.7. Actualizar la URL en Astro y desplegar

En el entorno de producción de tu web:

```env
PUBLIC_API_URL=https://api.tudominio.com
```

Luego:

```bash
npm run build
```

y despliega como lo hagas normalmente. Si es hosting con panel, vuelve a desplegar después de cambiar la variable.

## 3.8. Restringir CORS (recomendado en producción)

Por defecto la API acepta peticiones desde cualquier origen (`CORS_ORIGINS="*"`).
Para producción, define la variable de entorno con tus dominios separados por coma:

```bash
export CORS_ORIGINS="https://tudominio.com,https://www.tudominio.com"
```

Si usas systemd, añádela al servicio:

```ini
[Service]
Environment=CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

Reinicia el servicio:

```bash
sudo systemctl restart macollo-api
```

La API ya permite el encabezado `X-API-Key` en las peticiones CORS.

Nota: con `CORS_ORIGINS="*"` no uses `credentials: "include"` en el `fetch`, porque el navegador lo rechaza. El componente de esta guía no lo usa.

## 3.9. Opción sin CORS ni HTTPS en la API: proxy desde Astro

Si tu Astro corre en modo servidor (SSR) en el mismo VPS que la API, puedes evitar CORS y mixed content.
Crea `src/pages/api/analizar.ts`:

```ts
import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  const entrada = await request.formData();
  const archivo = entrada.get("file");

  if (!(archivo instanceof File)) {
    return new Response(JSON.stringify({ error: "Falta el archivo" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const form = new FormData();
  form.append("file", archivo, archivo.name);
  form.append("temperature_c", String(entrada.get("temperature_c") ?? "20"));
  form.append("crop", "gulupa");
  form.append("profile", String(entrada.get("profile") ?? "trips"));

  const res = await fetch("http://127.0.0.1:8000/api/predict", {
    method: "POST",
    headers: { "X-API-Key": process.env.TRIPS_API_KEY ?? "" },
    body: form,
  });

  return new Response(await res.text(), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
};
```

En el cliente, envía la foto a `/api/analizar` (mismo origen) en vez de a la API directa.
Esto **no funciona** si tu web es 100% estática: el servidor de Astro no existe en ese caso.
Requiere Node 20 o superior (para que `File` exista en el servidor).

---

# PARTE 4 — Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `model_loaded: false` | El modelo aún carga | Espera 1–2 min y vuelve a consultar `/api/health` |
| `Failed to fetch` en el navegador | API apagada o URL mal | Verifica `PUBLIC_API_URL`, que uvicorn corra y reinicia `npm run dev` |
| Error de CORS | Origen no permitido o credenciales | Revisa `CORS_ORIGINS`; no uses `credentials: "include"` con `*` |
| `Mixed Content` | Web HTTPS llamando API HTTP | Publica la API con HTTPS (Caddy/Nginx o Cloudflare Tunnel) |
| `413 Payload Too Large` | Proxy limita el tamaño | Sube `max_size` en Caddy o `client_max_body_size` en Nginx |
| `422 Unprocessable Entity` | Falta el campo `file` | Envía `multipart/form-data` con la clave `file` |
| `500` en `/api/predict` | Imagen corrupta o formato raro | Usa JPG/PNG/WebP/BMP; revisa los logs del servidor |
| No carga desde el celular | `localhost` o firewall | Usa `http://IP-DE-TU-PC:8000` y abre el puerto en la red local |
| Va lento | CPU sin GPU | Es normal en CPU (~2 s por imagen); usa un equipo con más RAM/GPU |
| Se cae por memoria | Modelo cargado varias veces | Un solo worker y ≥8 GB de RAM |
| El resultado no corresponde al perfil | No se envió `profile` o la galería está en otra carpeta | Envía `profile=trips`, `moscas` o `aranas_rojas` y usa el `label` correcto |
| Siempre devuelve el mismo objetivo | Umbral/confianza mal calibrados o pocas fotos | Agrega fotos reales al perfil y ajusta `min_confidence`/`min_margin` |

Ver logs en local:

```bash
# En la terminal donde corre uvicorn
# o si usas systemd:
journalctl -u macollo-api -n 100 --no-pager
```

---

# PARTE 5 — Checklist final

## Local

- [ ] `source .venv/bin/activate` funciona.
- [ ] `/api/health` responde `"model_loaded": true` y lista los tres perfiles.
- [ ] `/api/profiles` devuelve `trips`, `moscas` y `aranas_rojas`.
- [ ] `/docs` abre en el navegador.
- [ ] Una foto real devuelve `200` y un JSON coherente para cada perfil.
- [ ] `python -m unittest discover -s backend/tests -v` da `Ran 23 tests ... OK`.
- [ ] La galería tiene fotos y `POST /api/gallery/reindex` las indexa.
- [ ] `/api/gallery/labels` muestra las carpetas de los tres perfiles.

## Web

- [ ] `.env` tiene `PUBLIC_API_URL` correcta y sin `/` final.
- [ ] El dev server de Astro se reinició después de cambiar `.env`.
- [ ] El componente envía `file`, `temperature_c`, `crop` y `profile`.
- [ ] La consola del navegador no muestra errores de CORS ni `Failed to fetch`.
- [ ] La foto se ve en la respuesta (`detected_stage`, `detection.confidence`).

## Producción

- [ ] La API corre con systemd y se reinicia sola.
- [ ] `https://api.tudominio.com/api/health` responde.
- [ ] El certificado HTTPS es válido.
- [ ] El puerto `8000` no está abierto a internet.
- [ ] `PUBLIC_API_URL` apunta a HTTPS y se reconstruyó el sitio.
- [ ] CORS restringido a tu dominio.
- [ ] Hay respaldo de `data/reference_gallery/`.

> Para una prueba rápida desde otra red o desde otra página web sin abrir puertos,
> sigue la guía [Cloudflare Tunnel para prototipos](./docs/CLOUDFLARE-TUNNEL.md).

---

# PARTE 6 — Referencia rápida de la API

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/auth/login` | Inicia sesión del panel (sin registro público) |
| `POST` | `/api/auth/logout` | Cierra la sesión |
| `GET` | `/api/auth/me` | Devuelve el usuario autenticado |
| `GET` | `/api/health` | Estado del servicio, modelo y perfiles (público) |
| `GET` | `/api/catalog` | Catálogo completo de perfiles, objetivos y estadios (público) |
| `GET` | `/api/profiles` | Lista de perfiles de detección (público) |
| `GET` | `/api/profiles/{key}` | Detalle de un perfil (público) |
| `POST` | `/api/predict` | Analiza una foto. Requiere `X-API-Key` o sesión |
| `GET` | `/api/keys` | Lista API keys (requiere sesión) |
| `POST` | `/api/keys` | Crea una API key (requiere sesión) |
| `DELETE` | `/api/keys/{id}` | Revoca una API key (requiere sesión) |
| `GET` | `/api/gallery` | Estado y conteo de la galería (requiere sesión) |
| `GET` | `/api/gallery/items` | Lista las fotos indexadas (requiere sesión) |
| `GET` | `/api/gallery/labels` | Carpetas válidas por perfil; acepta `?profile=` (requiere sesión) |
| `POST` | `/api/gallery/upload` | Sube una foto de referencia con `label` o `profile+target+stage` (requiere sesión) |
| `POST` | `/api/gallery/reindex` | Reindexa todas las fotos locales (requiere sesión) |
| `GET` | `/api/handbook` | Ficha y ciclo por `profile` y `temperature_c` (requiere `X-API-Key` o sesión) |
| `GET` | `/api/gulupa-handbook` | Alias histórico de trips (requiere `X-API-Key` o sesión) |
| `GET` | `/docs` | Swagger interactivo |

Campos principales de la respuesta de `/api/predict`:

- `profile`: perfil usado (`trips`, `moscas` o `aranas_rojas`).
- `crop`: cultivo analizado (`gulupa`).
- `detection`: contrato genérico 2.x con `category`, `is_positive`, `confidence`, `is_uncertain`, `target_key`, `target_name`, `scientific_name`, `profile_experimental` y `scores`.
- `is_thrips`: si se confirmó trips (solo perfil `trips`, compatibilidad 1.x).
- `thrips_confidence`: confianza de trips (solo perfil `trips`, compatibilidad 1.x).
- `detected_target`: especie o categoría detectada.
- `detected_stage`: estadio biológico.
- `stage_confidence`: confianza del estadio (0–1).
- `is_damage_manifestation`: si es daño en fruto/flor.
- `cycle_info`: temperatura, duración del estadio, días para adulto y urgencia.
- `recommendations`: control biológico, etológico, cultural, biorracional y alerta de exportación.
- `exemplar_matches`: fotos de tu galería más parecidas (filtradas por perfil).
- `diagnostics`: modelo, dispositivo, probabilidades y tiempo.
- `inference_time_ms`: tiempo de inferencia.

---

# Limitaciones actuales (léelas antes de confiar ciegamente)

1. **Calibración de confianza por perfil:** cada perfil define su umbral (`min_confidence`) y margen (`min_margin`). Con fotos reales y una galería propia mejora, pero conviene calibrar cada perfil con una muestra etiquetada antes de confiar en él en producción.
2. **Autenticación:** `/api/predict` y `/api/handbook` exigen `X-API-Key` o sesión de panel; `/api/health`, `/api/catalog` y `/api/profiles` son públicos. Mantén las claves fuera del código, usa claves dedicadas por integración y revócalas si se filtran.
3. **Tamaño y tasa:** la API limita el tamaño de subida (`MAX_UPLOAD_BYTES`, 15 MB por defecto) con validación MIME y extensión. No hay rate limiting integrado: si publicas la API, añade límites en el proxy o en Cloudflare.
4. **El modelo es genérico:** BioCLIP 2.5 es zero-shot. La precisión real para trips, moscas o arañas rojas depende de tus fotos de referencia y de la calidad de la imagen (luz, acercamiento, enfoque). La galería de `moscas` y `aranas_rojas` empieza vacía hasta que subas muestras.
5. **CPU:** la inferencia tarda ~2 s por foto. Si necesitas muchos usuarios simultáneos, usa GPU o una cola de trabajos.
