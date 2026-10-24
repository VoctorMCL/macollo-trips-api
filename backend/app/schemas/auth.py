"""
Modelos Pydantic para autenticación, sesiones y gestión de API keys.
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario del administrador configurado en el servidor")
    password: str = Field(..., description="Contraseña de acceso")


class LoginResponse(BaseModel):
    authenticated: bool = Field(..., description="Estado de autenticación")
    username: str = Field(..., description="Nombre del usuario autenticado")


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="Nombre o identificador descriptivo del cliente")


class ApiKeyPublic(BaseModel):
    id: str = Field(..., description="Identificador único de la clave")
    name: str = Field(..., description="Nombre descriptivo asignado")
    key_prefix: str = Field(..., description="Prefijo visible de la clave (ej. mk_xxxxxxxx)")
    created_at: str = Field(..., description="Fecha de creación ISO-8601")
    created_by: str = Field(..., description="Usuario que emitió la clave")
    last_used_at: Optional[str] = Field(None, description="Fecha de último uso registrado ISO-8601")
    active: bool = Field(..., description="Estado de activación de la clave")


class ApiKeyCreateResponse(BaseModel):
    message: str = Field(..., description="Instrucción de seguridad para guardar la clave")
    raw_key: str = Field(..., description="Clave secreta completa (se muestra una sola vez)")
    key: ApiKeyPublic = Field(..., description="Metadatos públicos de la clave")


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyPublic] = Field(default_factory=list, description="Lista de claves de API registradas")
