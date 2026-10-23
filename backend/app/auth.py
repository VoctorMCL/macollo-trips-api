"""
Autenticación de la API: sesión de administrador (web) y API keys para clientes externos.
No hay registro público: las credenciales del panel se configuran por variables de entorno
y las claves de API se generan desde el panel autenticado.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Cookie, Header, HTTPException, status

from backend.app.config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    API_KEYS_PATH,
    AUTH_SECRET_PATH,
    DATA_DIR,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
)

_SECRET_CACHE: Optional[bytes] = None
VALID_API_KEY_PREFIX = "mk_"


def _get_secret() -> bytes:
    """Obtiene el secreto de firma desde el entorno o desde un archivo local persistente."""
    global _SECRET_CACHE
    if _SECRET_CACHE is not None:
        return _SECRET_CACHE

    env_secret = os.getenv("AUTH_SECRET_KEY")
    if env_secret:
        _SECRET_CACHE = env_secret.encode("utf-8")
        return _SECRET_CACHE

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if AUTH_SECRET_PATH.exists():
        _SECRET_CACHE = AUTH_SECRET_PATH.read_bytes()
    else:
        _SECRET_CACHE = secrets.token_bytes(32)
        AUTH_SECRET_PATH.write_bytes(_SECRET_CACHE)
        try:
            AUTH_SECRET_PATH.chmod(0o600)
        except OSError:
            pass
    return _SECRET_CACHE


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_session_token(username: str) -> str:
    payload = json.dumps(
        {"sub": username, "exp": int(time.time()) + SESSION_TTL_SECONDS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded = _b64encode(payload)
    signature = hmac.new(_get_secret(), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_b64encode(signature)}"


def verify_session_token(token: Optional[str]) -> Optional[str]:
    if not token or "." not in token:
        return None
    encoded, signature = token.rsplit(".", 1)
    expected = hmac.new(_get_secret(), encoded.encode("ascii"), hashlib.sha256).digest()
    try:
        provided = _b64decode(signature)
    except Exception:
        return None
    if not hmac.compare_digest(provided, expected):
        return None
    try:
        payload = json.loads(_b64decode(encoded).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    username = payload.get("sub")
    return username if isinstance(username, str) and username else None


def authenticate_admin(username: str, password: str) -> bool:
    user_ok = hmac.compare_digest(username.encode("utf-8"), ADMIN_USERNAME.encode("utf-8"))
    pass_ok = hmac.compare_digest(password.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
    return user_ok and pass_ok


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _load_api_keys() -> List[Dict[str, Any]]:
    if not API_KEYS_PATH.exists():
        return []
    try:
        data = json.loads(API_KEYS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_api_keys(keys: List[Dict[str, Any]]) -> None:
    API_KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = API_KEYS_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(keys, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        tmp_path.chmod(0o600)
    except OSError:
        pass
    tmp_path.replace(API_KEYS_PATH)


def create_api_key(name: str, created_by: str) -> Dict[str, Any]:
    raw_key = VALID_API_KEY_PREFIX + secrets.token_urlsafe(32)
    entry = {
        "id": secrets.token_hex(8),
        "name": name.strip()[:80] or "Clave sin nombre",
        "key_prefix": raw_key[:12],
        "key_hash": _hash_api_key(raw_key),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": created_by,
        "last_used_at": None,
        "active": True,
    }
    keys = _load_api_keys()
    keys.append(entry)
    _save_api_keys(keys)
    return {"raw_key": raw_key, "key": _public_key(entry)}


def verify_api_key(raw_key: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw_key or not raw_key.startswith(VALID_API_KEY_PREFIX):
        return None
    incoming_hash = _hash_api_key(raw_key)
    keys = _load_api_keys()
    for entry in keys:
        if not entry.get("active", True):
            continue
        if hmac.compare_digest(str(entry.get("key_hash", "")), incoming_hash):
            entry["last_used_at"] = datetime.now(timezone.utc).isoformat()
            _save_api_keys(keys)
            return _public_key(entry)
    return None


def _public_key(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "key_prefix": entry.get("key_prefix"),
        "created_at": entry.get("created_at"),
        "created_by": entry.get("created_by"),
        "last_used_at": entry.get("last_used_at"),
        "active": bool(entry.get("active", True)),
    }


def list_api_keys() -> List[Dict[str, Any]]:
    return [_public_key(entry) for entry in _load_api_keys()]


def revoke_api_key(key_id: str) -> bool:
    keys = _load_api_keys()
    found = False
    for entry in keys:
        if entry.get("id") == key_id:
            entry["active"] = False
            found = True
            break
    if found:
        _save_api_keys(keys)
    return found


def _session_username(session_token: Optional[str]) -> Optional[str]:
    return verify_session_token(session_token)


def require_session(
    session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    """Exige una sesión de panel válida (para galería y administración de claves)."""
    username = _session_username(session)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes iniciar sesión para acceder a este recurso.",
        )
    return username


def require_api_access(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Dict[str, Any]:
    """Permite el acceso con una API key válida o con una sesión web autenticada."""
    api_key = verify_api_key(x_api_key)
    if api_key:
        return {"type": "api_key", "key": api_key}

    username = _session_username(session)
    if username:
        return {"type": "session", "user": username}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acceso denegado. Envía una API key válida en X-API-Key o inicia sesión.",
    )
