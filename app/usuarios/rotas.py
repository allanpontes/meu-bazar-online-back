from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.seguranca import HASH_FALSO, criar_token_acesso, gerar_hash_senha, verificar_senha
from app.usuarios.modelos import Usuario
from app.usuarios.schemas import UsuarioCreate, UsuarioResponse, LoginRequest, TokenResponse

router = APIRouter()

@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_admin(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se o email já existe
    existe = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    
    novo_usuario = Usuario(email=usuario.email, senha_hash=gerar_hash_senha(usuario.senha), is_admin=True)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

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
