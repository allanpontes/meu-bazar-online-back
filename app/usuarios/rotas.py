from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.seguranca import HASH_FALSO, criar_token_acesso, verificar_senha
from app.usuarios.modelos import Usuario
from app.usuarios.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    senha_correta = verificar_senha(dados.senha, usuario.senha_hash if usuario else HASH_FALSO)
    if not usuario or not senha_correta or not usuario.is_admin:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    return TokenResponse(
        access_token=criar_token_acesso(usuario.id, usuario.is_admin),
        expires_in=settings.JWT_EXPIRA_MINUTOS * 60,
    )
