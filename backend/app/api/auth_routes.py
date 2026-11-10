"""Rutas de autenticación del panel y administración de API keys."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.auth import (
    authenticate_admin,
    create_api_key,
    create_session_token,
    list_api_keys,
    require_session,
    revoke_api_key,
)
from backend.app.config import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_SECONDS,
)
from backend.app.schemas import ApiKeyCreateRequest, LoginRequest

router = APIRouter(tags=["Autenticación"])


@router.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    """Inicia sesión con las credenciales del administrador configuradas en el servidor."""

    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )

    token = create_session_token(payload.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
    )
    return {"authenticated": True, "username": payload.username}


@router.post("/auth/logout")
async def logout(response: Response):
    """Cierra la sesión del panel."""

    response.delete_cookie(
        SESSION_COOKIE_NAME, secure=SESSION_COOKIE_SECURE, samesite="lax"
    )
    return {"authenticated": False}


@router.get("/auth/me")
async def auth_me(username: str = Depends(require_session)):
    """Devuelve el usuario autenticado actual."""

    return {"authenticated": True, "username": username}


@router.get("/keys")
async def get_api_keys(_username: str = Depends(require_session)):
    """Lista las claves de API emitidas (sin mostrar la clave completa)."""

    return {"items": list_api_keys()}


@router.post("/keys")
async def create_new_api_key(
    payload: ApiKeyCreateRequest, username: str = Depends(require_session)
):
    """Genera una nueva API key. La clave completa solo se muestra una vez."""

    created = create_api_key(payload.name, username)
    return {
        "message": "API key creada. Guárdala ahora: no se volverá a mostrar.",
        "raw_key": created["raw_key"],
        "key": created["key"],
    }


@router.delete("/keys/{key_id}")
async def delete_api_key(key_id: str, _username: str = Depends(require_session)):
    """Revoca una API key existente."""

    if not revoke_api_key(key_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key no encontrada."
        )
    return {"message": "API key revocada correctamente."}
