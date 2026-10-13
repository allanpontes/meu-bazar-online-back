import secrets
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings

def exigir_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Área administrativa não configurada.")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso administrativo negado.")
