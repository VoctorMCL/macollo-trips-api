# 🌐 Guía: exponer la API con Cloudflare Tunnel para un prototipo

Esta guía sirve para publicar temporalmente la API de **Macollo Visión Fitosanitaria**
en internet con HTTPS y probarla desde **otra página web** (Astro, React, Vercel,
GitHub Pages, WordPress, etc.) sin abrir puertos en el router ni contratar un servidor.

> **Caso de uso:** prototipo o prueba con un agrónomo, un cliente o un compañero
> que está en otra red. No es la configuración recomendada para producción
> permanente, aunque el mismo túnel puede evolucionar a una URL fija con dominio propio.

---

## 0. Resumen rápido (5 minutos)

En tres terminales:

```bash
# Terminal 1 — API local (sin --reload para un prototipo estable)
cd /home/victormcl/Documents/macollo-trips-api
source .venv/bin/activate
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — túnel temporal de Cloudflare
cloudflared tunnel --url http://127.0.0.1:8000

# Terminal 3 — comprobar que el túnel responde
curl https://LA-URL-QUE-DEVOLVIO-CLOUDFLARED/api/health
```

La terminal 2 mostrará una URL parecida a:

```text
https://palabras-aleatorias.trycloudflare.com
```

Esa es la URL pública de la API. Se usa en la otra página así:

```js
const API_BASE = "https://palabras-aleatorias.trycloudflare.com";
const API_KEY = "mk_tu_clave_generada_en_el_panel";
```

> Cada vez que reinicies el túnel rápido, **la URL cambia**. Si necesitas una URL
> fija, usa la opción con dominio propio de la sección 6.

---

## 1. Qué hace exactamente el túnel

```text
Otra página web (HTTPS)
        │
        │  POST https://xxx.trycloudflare.com/api/predict
        ▼
Cloudflare (TLS + túnel)
        │
        ▼
cloudflared en tu PC
        │
        ▼
http://127.0.0.1:8000  ← FastAPI + BioCLIP 2.5
```

Ventajas para el prototipo:

- HTTPS real: la cámara del celular funciona (los navegadores exigen HTTPS).
- No hay que abrir el puerto 8000 en el router.
- No hace falta IP pública ni dominio.
- Cloudflare Tunnel es gratuito.

Limitaciones del túnel rápido (`trycloudflare.com`):

- La URL es aleatoria y cambia al reiniciar.
- No tiene SLA ni garantías.
- Cualquiera que tenga la URL puede llegar al login del panel.
- No se puede combinar con Cloudflare Access en el modo rápido.

---

## 2. Instalar `cloudflared`

### Linux (este equipo: x86_64)

```bash
curl -L -o /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

sudo dpkg -i /tmp/cloudflared.deb
cloudflared --version
```

Si prefieres el binario sin paquete:

```bash
sudo curl -L -o /usr/local/bin/cloudflared \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64

sudo chmod +x /usr/local/bin/cloudflared
cloudflared --version
```

### macOS

```bash
brew install cloudflared
```

### Windows

```powershell
winget install --id Cloudflare.cloudflared
```

---

## 3. Preparar la API para el prototipo

### 3.1. Variables recomendadas

Antes de arrancar, define una contraseña de administrador distinta a la de fábrica.
En la misma terminal:

```bash
cd /home/victormcl/Documents/macollo-trips-api
source .venv/bin/activate

export ADMIN_USERNAME="admin_prototipo"
export ADMIN_PASSWORD="UnaClaveLargaYUnica_2026"
export SESSION_COOKIE_SECURE="true"
export CORS_ORIGINS="*"
```

> `CORS_ORIGINS="*"` es aceptable **solo para el prototipo**, para no bloquear la
> página mientras averiguas su URL. Cuando la tengas, restringe el origen
> (ver sección 5).

> `SESSION_COOKIE_SECURE="true"` hace que la cookie del panel solo viaje por HTTPS.
> Funciona a través del túnel, pero si también abres `http://localhost:8000`
> el login local no conservará la sesión. Para probar en local sin túnel usa
> `SESSION_COOKIE_SECURE="false"`.

### 3.2. Arrancar FastAPI

```bash
.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Usar `127.0.0.1` evita que la API quede expuesta a toda la red Wi-Fi; solo
`cloudflared` podrá llegar a ella. Si necesitas además probar desde el celular
en la misma red, usa `--host 0.0.0.0`.

Espera a ver en la terminal:

```text
[BioCLIPEngine] Modelo hf-hub:imageomics/bioclip-2.5-vith14 listo.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

La primera carga puede tardar 1–2 minutos. Comprueba en otra terminal:

```bash
curl http://127.0.0.1:8000/api/health
```

Debe responder `"status": "healthy"` y `"model_loaded": true`.

---

## 4. Levantar el túnel rápido

En una terminal nueva:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Verás un bloque como este:

```text
Your quick Tunnel has been created! Visit it at:
https://nombre-aleatorio.trycloudflare.com
```

Guarda esa URL. Es la base de la API:

```text
https://nombre-aleatorio.trycloudflare.com/api/health
https://nombre-aleatorio.trycloudflare.com/docs
https://nombre-aleatorio.trycloudflare.com/          ← panel web
```

### Comprobar desde fuera

```bash
export TUNNEL_URL="https://nombre-aleatorio.trycloudflare.com"

curl "$TUNNEL_URL/api/health"
curl "$TUNNEL_URL/api/profiles"
```

Si `api/health` responde pero `api/profiles` también, el túnel está bien.
Abre el panel desde el celular usando datos móviles (no la misma Wi-Fi) para
confirmar que realmente es accesible desde internet.

> Si el túnel devuelve `502` o `1033`, normalmente la API aún está cargando el
> modelo o no está corriendo en el puerto correcto.

---

## 5. Configurar CORS para la otra página

### 5.1. Por qué hace falta

La otra página se sirve desde otro origen, por ejemplo:

```text
https://mi-otra-pagina.pages.dev
```

Y llama a:

```text
https://nombre-aleatorio.trycloudflare.com/api/predict
```

El navegador enviará primero una petición `OPTIONS` (preflight) porque se usa
el encabezado `X-API-Key`. FastAPI debe responder con el origen permitido.

### 5.2. Opción rápida para el prototipo

Deja:

```bash
export CORS_ORIGINS="*"
```

Reinicia la API si cambiaste la variable. Con `allow_credentials=False` (la
configuración actual), `*` es válido para peticiones con `X-API-Key`.

### 5.3. Opción recomendada cuando ya conoces la URL

```bash
export CORS_ORIGINS="https://mi-otra-pagina.pages.dev,http://localhost:5173"
```

Reglas importantes:

- Incluye **esquema + dominio + puerto**, sin `/` final.
- Separa varios orígenes con coma, sin espacios.
- Si la página cambia de dominio, actualiza la variable y reinicia la API.
- No uses `*` si la página necesita cookies de sesión (`allow_credentials`);
  para ese caso usa orígenes explícitos.

### 5.4. Probar el preflight manualmente

```bash
curl -i -X OPTIONS "$TUNNEL_URL/api/predict" \
  -H "Origin: https://mi-otra-pagina.pages.dev" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: x-api-key"
```

Debes ver algo similar a:

```text
HTTP/2 200
access-control-allow-origin: https://mi-otra-pagina.pages.dev
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT, QUERY
access-control-allow-headers: x-api-key
```

Si usas `CORS_ORIGINS="*"`, el valor de `access-control-allow-origin` será `*`;
también es válido para el prototipo porque las llamadas usan `X-API-Key` y no
cookies. Si no aparece `access-control-allow-origin`, revisa `CORS_ORIGINS` y
reinicia la API.

---

## 6. URL fija con dominio propio (opcional)

Si ya tienes un dominio administrado en Cloudflare, puedes crear un túnel con
nombre y una URL estable:

```bash
cloudflared tunnel login
cloudflared tunnel create macollo-prototipo
```

Crea la ruta DNS:

```bash
cloudflared tunnel route dns macollo-prototipo api-prototipo.tudominio.com
```

Crea `~/.cloudflared/config.yml` (usa el UUID que imprimió `cloudflared tunnel create`; también puedes consultarlo con `cloudflared tunnel list`):

```yaml
tunnel: REEMPLAZA-CON-EL-UUID
credentials-file: /home/victormcl/.cloudflared/REEMPLAZA-CON-EL-UUID.json

ingress:
  - hostname: api-prototipo.tudominio.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Arranca el túnel:

```bash
cloudflared tunnel run macollo-prototipo
```

Ahora la URL es fija:

```text
https://api-prototipo.tudominio.com
```

Configura CORS con ese dominio:

```bash
export CORS_ORIGINS="https://mi-otra-pagina.pages.dev"
```

### Dejarlo corriendo en segundo plano

Para una prueba corta:

```bash
nohup cloudflared tunnel run macollo-prototipo \
  > /tmp/cloudflared-macollo.log 2>&1 &
```

Para que sobreviva reinicios, crea un servicio systemd:

```ini
# /etc/systemd/system/cloudflared-macollo.service
[Unit]
Description=Cloudflare Tunnel Macollo Prototipo
After=network.target

[Service]
Type=simple
User=victormcl
ExecStart=/usr/bin/cloudflared tunnel --config /home/victormcl/.cloudflared/config.yml run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cloudflared-macollo.service
sudo systemctl status cloudflared-macollo.service
```

> La API también debe quedar corriendo de forma persistente. Puedes usar el
> servicio systemd de `docs/DEPLOYMENT.md` apuntando a `127.0.0.1:8000`.

---

## 7. Crear la API key para la otra página

La otra página **no debe usar usuario y contraseña del panel**. Debe usar una
API key enviada en el encabezado `X-API-Key`.

### Opción A — desde el panel web

1. Abre `https://TU-TUNEL/`.
2. Inicia sesión con `ADMIN_USERNAME` y `ADMIN_PASSWORD`.
3. Ve a **API y accesos**.
4. Crea una clave, por ejemplo `Prototipo página externa`.
5. Copia la clave `mk_...` en ese momento; no se vuelve a mostrar.

### Opción B — por terminal

```bash
# Guardar cookie de sesión
curl -c cookies.txt -X POST "$TUNNEL_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_prototipo","password":"UnaClaveLargaYUnica_2026"}'

# Crear API key
curl -b cookies.txt -X POST "$TUNNEL_URL/api/keys" \
  -H "Content-Type: application/json" \
  -d '{"name":"Prototipo pagina externa"}'
```

La respuesta contiene `raw_key`. Ese valor es el que usa la otra página.

---

## 8. Consumir el túnel desde la otra página

### 8.1. Variables de entorno

En el proyecto de la otra página:

```env
# Astro
PUBLIC_API_URL=https://nombre-aleatorio.trycloudflare.com
PUBLIC_MACOLLO_API_KEY=mk_tu_clave

# Vite / React
VITE_API_URL=https://nombre-aleatorio.trycloudflare.com
VITE_MACOLLO_API_KEY=mk_tu_clave
```

Sin `/` al final. Si usas Astro, recuerda reconstruir después de cambiar
variables `PUBLIC_*`.

### 8.2. Ejemplo de llamada

```js
const API_BASE = import.meta.env.PUBLIC_API_URL; // o VITE_API_URL
const API_KEY = import.meta.env.PUBLIC_MACOLLO_API_KEY;

async function analizarFoto(file, perfil = "trips") {
  const form = new FormData();
  form.append("file", file, "muestra.jpg");
  form.append("temperature_c", "22.5");
  form.append("crop", "gulupa");
  form.append("profile", perfil); // trips | moscas | aranas_rojas

  const response = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    headers: {
      // No agregues Content-Type manualmente: el navegador pone el boundary.
      "X-API-Key": API_KEY,
    },
    body: form,
  });

  if (!response.ok) {
    const detalle = await response.text();
    throw new Error(`Error ${response.status}: ${detalle}`);
  }

  return response.json();
}
```

Uso:

```js
const resultado = await analizarFoto(archivo, "trips");
const deteccion = resultado.detection;

console.log(deteccion.profile);        // "trips"
console.log(deteccion.target_name);    // objetivo detectado
console.log(deteccion.is_positive);    // true/false
console.log(deteccion.confidence);     // 0.0 – 1.0
console.log(resultado.detected_stage); // estadio
console.log(resultado.cycle_info);     // ciclo térmico
console.log(resultado.recommendations);// plan MIP
```

Para moscas de la fruta:

```js
await analizarFoto(archivo, "moscas");
```

Para arañas rojas:

```js
await analizarFoto(archivo, "aranas_rojas");
```

### 8.3. Ejemplo con `curl`

```bash
curl -X POST "$TUNNEL_URL/api/predict" \
  -H "X-API-Key: mk_tu_clave" \
  -F "file=@/ruta/a/foto.jpg" \
  -F "temperature_c=22.5" \
  -F "crop=gulupa" \
  -F "profile=trips"
```

---

## 9. Checklist de prueba del prototipo

### En tu equipo

- [ ] `curl http://127.0.0.1:8000/api/health` responde `healthy`.
- [ ] `cloudflared tunnel --url ...` muestra una URL `https://...trycloudflare.com`.
- [ ] `curl "$TUNNEL_URL/api/health"` responde.
- [ ] `curl "$TUNNEL_URL/api/profiles"` lista los tres perfiles.
- [ ] El panel abre en el navegador y permite iniciar sesión.
- [ ] Se creó una API key y se copió completa.

### Desde la otra página

- [ ] La URL configurada es HTTPS y no termina en `/`.
- [ ] La petición incluye `X-API-Key`.
- [ ] El preflight `OPTIONS` devuelve `access-control-allow-origin`.
- [ ] La consola del navegador no muestra errores de CORS ni `Failed to fetch`.
- [ ] `POST /api/predict` devuelve `200` con `detection`.
- [ ] La foto se envía como `FormData` sin `Content-Type` manual.
- [ ] Se probaron `trips`, `moscas` y `aranas_rojas`.

### Desde el celular, fuera de la red local

- [ ] Abre la URL del túnel con datos móviles.
- [ ] El panel carga por HTTPS.
- [ ] La cámara se activa (el túnel da contexto seguro).
- [ ] Una foto se procesa y muestra el diagnóstico.

---

## 10. Seguridad mínima para el prototipo

1. **Cambia la contraseña del panel.** No publiques `admin` / `macollo2026`.
2. **No abras el puerto 8000** en el router; el túnel es el único acceso.
3. **Usa una API key por página o cliente.** Revócala al terminar la prueba.
4. **Restringe CORS** al dominio de la otra página cuando lo conozcas.
5. **Detén el túnel** cuando no lo estés usando (`Ctrl + C`).
6. **No pongas la API key en un repositorio público** si la página es pública:
   cualquiera puede leerla en el navegador. Para el prototipo es aceptable;
   para producción, haz que la otra página llame a **su propio backend** o a un
   Cloudflare Worker que guarde la clave en el servidor.
7. **Cloudflare Access es opcional.** Si lo activas, las llamadas con `X-API-Key`
   también quedarán bloqueadas salvo que uses un *service token* o una política
   de bypass para `/api/*`. Para un prototipo simple, no lo actives.

---

## 11. Problemas frecuentes

| Síntoma | Causa probable | Solución |
| :--- | :--- | :--- |
| `502 Bad Gateway` o error `1033` | La API no está corriendo o el puerto no coincide. | Verifica `curl http://127.0.0.1:8000/api/health` y que el túnel apunte al puerto 8000. |
| El túnel abre pero la API tarda en responder | BioCLIP todavía está cargando el modelo. | Espera a `"model_loaded": true` en `/api/health`. |
| `Failed to fetch` en la otra página | URL HTTP, URL mal escrita o túnel caído. | Usa la URL HTTPS completa, sin `/` final, y comprueba el túnel. |
| Error de CORS | El origen no está en `CORS_ORIGINS`. | Agrega el dominio exacto y reinicia la API. |
| `401 Acceso denegado` | Falta `X-API-Key` o la clave es inválida/revocada. | Crea una clave nueva y envíala en el encabezado. |
| `404` al llamar `/api/...` | El túnel apunta a otro servicio o falta el prefijo `/api`. | Revisa la URL y el `--url` de `cloudflared`. |
| La URL del túnel dejó de funcionar | El túnel rápido se reinició. | Copia la nueva URL y actualízala en la otra página. |
| El login del panel no persiste | `SESSION_COOKIE_SECURE=true` y estás probando por HTTP local. | Usa el túnel HTTPS o pon la variable en `false` solo para local. |
| Cloudflare muestra pantalla de login en las llamadas API | Cloudflare Access está activo. | Usa un service token o desactiva Access para el prototipo. |
| La cámara no abre en el celular | La página se sirve por HTTP. | Usa la URL HTTPS del túnel. |

---

## 12. Referencias

- [Cloudflare Tunnel — documentación oficial](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Túneles rápidos (`trycloudflare.com`)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/)
- [Guía general de conexión web del proyecto](../GUIA_CONEXION_WEB.md)
- [Guía de despliegue](./DEPLOYMENT.md)
- [Referencia de endpoints](./ENDPOINTS.md)
