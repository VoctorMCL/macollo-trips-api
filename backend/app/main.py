"""
Servidor principal FastAPI de Macollo Visión Fitosanitaria.

El catálogo de perfiles permite detectar trips, moscas de la fruta y arañas
rojas, y añadir otros objetivos sin reescribir el motor.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.auth_routes import router as auth_router
from backend.app.api.catalog_routes import router as catalog_router
from backend.app.api.gallery_routes import router as gallery_router
from backend.app.api.health_routes import router as health_router
from backend.app.api.prediction_routes import router as prediction_router
from backend.app.config import (
    CORS_ORIGINS,
    DEFAULT_PROFILE,
    STATIC_DIR,
    settings,
)
from backend.app.domain.catalog import DEFAULT_PROFILE_KEY
from backend.app.ml.bioclip_engine import bioclip_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{settings.app_name}] Iniciando servicio...")
    # Cargar BioCLIP 2.5 en un hilo en segundo plano para no bloquear el inicio
    # de Uvicorn. Esto garantiza que el puerto 8080 se abra en menos de 1 segundo
    # y Cloud Run apruebe el health check de inmediato sin dar timeout.
    # Las peticiones a /api/predict que lleguen durante la carga reciben 503
    # "warming" (con Retry-After) en lugar de quedarse colgadas.
    bioclip_engine.ensure_load_started()
    yield
    print(f"[{settings.app_name}] Deteniendo servicio...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "API de visión artificial con BioCLIP 2.5 para detección de trips, "
        "moscas de la fruta, arañas rojas, estadios biológicos y manejo fitosanitario."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_ui_cache(request, call_next):
    """Evita que el navegador conserve HTML/CSS/JS viejos del panel."""

    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith(("/css/", "/js/", "/assets/")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/api", tags=["Estado"])
async def api_root():
    """Resumen de la API y enlaces útiles."""

    return {
        "app": settings.app_name,
        "version": settings.version,
        "default_profile": DEFAULT_PROFILE or DEFAULT_PROFILE_KEY,
        "docs": "/docs",
        "catalog": "/api/catalog",
        "profiles": "/api/profiles",
        "health": "/api/health",
    }


for router in (
    auth_router,
    health_router,
    catalog_router,
    gallery_router,
    prediction_router,
):
    app.include_router(router, prefix="/api")


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")
