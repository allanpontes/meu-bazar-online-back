from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.usuarios.modelos import Usuario

# O bcrypt só considera os 72 primeiros bytes da senha
LIMITE_BYTES_SENHA = 72

def gerar_hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > LIMITE_BYTES_SENHA:
        raise ValueError("Senha longa demais.")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")

# Hash falso usado quando o e-mail não existe, para o login demorar igual e não revelar quais e-mails existem
HASH_FALSO = bcrypt.hashpw(b"senha-descartavel", bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > LIMITE_BYTES_SENHA:
        return False
    try:
        return bcrypt.checkpw(senha_bytes, senha_hash.encode("utf-8"))
    except ValueError:
        # Hash inválido no banco (ex.: senha antiga em texto puro) nunca autentica
        return False

def criar_token_acesso(usuario_id: int, is_admin: bool) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "is_admin": is_admin,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.JWT_EXPIRA_MINUTOS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITMO)

def decodificar_token(token: str) -> dict:
    # Fixar o algoritmo evita aceitar tokens assinados com "none" ou outro método
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITMO],
        options={"require": ["exp", "sub"]},
    )

esquema_bearer = HTTPBearer(auto_error=False)

def exigir_admin(
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    nao_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acesso administrativo negado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credenciais:
        raise nao_autorizado
    try:
        payload = decodificar_token(credenciais.credentials)
        usuario_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise nao_autorizado

    # Confere no banco: se a conta foi apagada ou deixou de ser admin, o token antigo deixa de valer
    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.is_admin:
        raise nao_autorizado
    return usuario
