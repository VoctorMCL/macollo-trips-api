# 📊 Diagramas de Secuencia — Macollo Visión Fitosanitaria API

Este documento presenta los flujos de interacción temporal entre los componentes del sistema mediante diagramas Mermaid estructurados.

---

## 1. Flujo de Inferencia Fitosanitaria en Tiempo Real

Ilustra la recepción de una foto de campo desde la cámara móvil, la autenticación, la proyección en el espacio latente de BioCLIP 2.5, la búsqueda de vecinos cercanos y la generación del dictamen agronómico para el perfil solicitado (`trips`, `moscas` o `aranas_rojas`).

```mermaid
sequenceDiagram
    autonumber
    actor Operario as 📱 Operario de Campo
    participant UI as Web App PWA (CameraUI)
    participant API as FastAPI Gateway (/api/predict)
    participant Auth as Validador de Acceso
    participant Bio as BioCLIP 2.5 Engine
    participant Gal as Gallery Index (k-NN)
    participant Agro as Motor Agronómico por Perfil

    Operario->>UI: Captura foto con retícula macro + Temperatura + Perfil
    UI->>API: POST /api/predict (multipart: file, temperature_c, profile, crop)
    API->>Auth: require_api_access(header, cookie)
    Auth-->>API: Autorizado (API Key válida o Sesión activa)
    
    API->>Bio: predict(image, profile, temperature_c)
    
    critical Extracción de Características
        Bio->>Bio: Preprocesamiento (Resize 224x224, Tensor Normalization)
        Bio->>Bio: ViT-H/14 Encode Image -> v_img (1024-d, L2=1.0)
    end

    critical Discriminación Taxonómica
        Bio->>Bio: Producto escalar vs prototipos del perfil seleccionado
        Bio->>Bio: Softmax con Logit Scale -> probabilidad por objetivo
    end

    opt Consulta a Memoria Empírica (Few-Shot)
        Bio->>Gal: query_nearest(v_img, top_k, profile)
        Gal-->>Bio: Ejemplares del mismo perfil con similitud y estadio
        Bio->>Bio: Calibrar confianza y estadio con voto de ejemplares
    end

    alt Objetivo positivo confirmado
        Bio->>Agro: get_cycle_estimate(perfil, estadio, temp_c)
        Agro-->>Bio: Días restantes, duración y nivel de urgencia
        Bio->>Agro: get_mip_recommendations(perfil, estadio, is_damage)
        Agro-->>Bio: Plan fitosanitario (Biológico, Etológico, Cultural, Químico IRAC)
    else Clase confusora, daño o tejido sano
        Bio->>Bio: Etiquetar objetivo detectado y marcar is_positive=false
    end

    Bio-->>API: Estructura de diagnóstico completa
    API-->>UI: 200 OK JSON (PredictionResponse con detection)
    UI-->>Operario: Renderiza banner de alerta, fase, días y recomendaciones
```

---

## 2. Flujo de Subida y Reindexación Vectorial de la Galería

Muestra cómo una nueva fotografía aportada por el usuario enriquece la memoria del modelo sin necesidad de reentrenamiento.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 👤 Administrador del Panel
    participant UI as Panel Web (GalleryUI)
    participant API as FastAPI (/api/gallery/upload)
    participant Disk as Almacenamiento en Disco
    participant Bio as BioCLIP Engine
    participant Gal as Gallery Index

    Admin->>UI: Selecciona perfil, objetivo y estadio, y arrastra una foto real
    UI->>API: POST /api/gallery/upload (file, label o profile+target+stage)
    
    API->>API: Resolver carpeta de galería con /api/gallery/labels
    API->>API: Validar extensión (.jpg/.png/.webp/.bmp) y sanitizar nombre
    API->>Disk: Guardar archivo en data/reference_gallery/{perfil}/{objetivo}/{estadio}/
    
    API->>Gal: rebuild_index(model, preprocess, device)
    
    loop Para cada foto del catálogo de galería
        Gal->>Disk: Leer imagen física
        Gal->>Bio: Extraer embedding con ViT-H/14
        Bio-->>Gal: Tensor normalizado 1024-d
    end

    Gal->>Disk: Guardar checkpoint consolidado en data/gallery_embeddings.pt
    Gal-->>API: Total de imágenes indexadas
    API-->>UI: 200 OK {message, label, profile, target, total_indexed_images}
    UI-->>Admin: Actualiza estadísticas por perfil/objetivo/estadio
```

---

## 3. Flujo de Inicio de Sesión y Emisión de API Keys

Muestra el protocolo de login sin registro público y la generación segura de tokens de cliente con hash SHA-256.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 👤 Administrador
    participant UI as Panel Web
    participant Auth as Módulo de Seguridad (auth.py)
    participant DB as data/api_keys.json

    Admin->>UI: Ingresa usuario y contraseña configurados en servidor
    UI->>Auth: POST /api/auth/login {username, password}
    Auth->>Auth: Validar credenciales con hmac.compare_digest()
    Auth->>Auth: Generar token de sesión firmado con HMAC-SHA256
    Auth-->>UI: Set-Cookie: macollo_session=<token>; HttpOnly; SameSite=Lax
    
    Note over Admin, UI: Administrador dentro del Panel (Sesión Activa)

    Admin->>UI: Ingresa nombre ("Portal Macollo") y presiona "Crear clave"
    UI->>Auth: POST /api/keys {name: "Portal Macollo"} (con Cookie)
    Auth->>Auth: Generar token aleatorio: raw_key = "mk_" + secrets.token_urlsafe(32)
    Auth->>Auth: key_hash = sha256(raw_key), prefix = raw_key[:12]
    Auth->>DB: Guardar {id, name, prefix, key_hash, created_at, active: true}
    Auth-->>UI: 200 OK {raw_key, key_metadata}
    UI-->>Admin: ⚠️ Muestra raw_key completa UNA SOLA VEZ para que la copie
```

---

## 4. Integración Externa: Plataforma Web Macollo llamando a la API

Ilustra la integración con una página web existente (ej. portal [Macollo](https://github.com/VoctorMCL/Macollo) en Astro/React) consumiendo predicciones y coordinando datos meteorológicos de SIATA o Open-Meteo.

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as 🌾 Usuario en Portal Macollo
    participant Web as Portal Web Macollo (Astro / Next.js)
    participant Weather as API SIATA / Open-Meteo
    participant TripsAPI as Macollo Visión Fitosanitaria API (FastAPI)

    Usuario->>Web: Carga sección "Diagnóstico de Campo"
    Web->>Weather: Consultar temperatura en tiempo real del lote
    Weather-->>Web: 21.5 °C
    
    Usuario->>Web: Selecciona perfil (trips/moscas/aranas_rojas) y adjunta foto macro
    
    Web->>TripsAPI: POST /api/predict<br/>Header: X-API-Key: mk_...<br/>Body: FormData(file, temperature_c=21.5, crop="gulupa", profile="trips")
    
    TripsAPI->>TripsAPI: Validar API Key y procesar BioCLIP 2.5
    TripsAPI-->>Web: 200 OK JSON con detection, ciclo en 21.5°C y recomendaciones MIP
    
    Web-->>Usuario: Muestra en pantalla el dictamen fitosanitario integrado
```
