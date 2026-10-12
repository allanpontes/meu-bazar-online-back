from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.usuarios.modelos import Usuario
from app.usuarios.schemas import UsuarioCreate, UsuarioResponse, LoginRequest

router = APIRouter()

@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_admin(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se o email já existe
    existe = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    
    # IMPORTANTE: Em produção, use criptografia (ex: passlib/bcrypt) para a senha!
    novo_usuario = Usuario(email=usuario.email, senha_hash=usuario.senha, is_admin=True)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if not usuario or usuario.senha_hash != dados.senha:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    
    return {
        "mensagem": "Autenticado com sucesso!",
        "token_simulado": f"token-secreto-bazar-{usuario.id}",
        "is_admin": usuario.is_admin
    }
