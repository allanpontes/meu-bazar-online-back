import secrets
from typing import Optional
import bcrypt
from fastapi import Header, HTTPException, status
from app.core.config import settings

# O bcrypt só considera os 72 primeiros bytes da senha
LIMITE_BYTES_SENHA = 72

def gerar_hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > LIMITE_BYTES_SENHA:
        raise ValueError("Senha longa demais.")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > LIMITE_BYTES_SENHA:
        return False
    try:
        return bcrypt.checkpw(senha_bytes, senha_hash.encode("utf-8"))
    except ValueError:
        # Hash inválido no banco (ex.: senha antiga em texto puro) nunca autentica
        return False

def exigir_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Área administrativa não configurada.")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso administrativo negado.")
