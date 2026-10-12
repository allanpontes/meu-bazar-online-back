import os

# 1. Cria a pasta do novo módulo de usuários
os.makedirs("app/usuarios", exist_ok=True)

# 2. Cria os arquivos do módulo de usuários
with open("app/usuarios/__init__.py", "w", encoding="utf-8") as f:
    f.write("")

with open("app/usuarios/modelos.py", "w", encoding="utf-8") as f:
    f.write("""from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios_bazar"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=True)
""")

with open("app/usuarios/schemas.py", "w", encoding="utf-8") as f:
    f.write("""from pydantic import BaseModel, EmailStr

class UsuarioBase(BaseModel):
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    senha: str
""")

with open("app/usuarios/rotas.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import APIRouter, Depends, HTTPException, status
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
""")

# 3. Atualiza os Modelos de Produtos com o campo 'status'
with open("app/produtos/modelos.py", "w", encoding="utf-8") as f:
    f.write("""from sqlalchemy import Column, Integer, String, Float
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.database import Base

def obter_hora_brasilia_str():
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return agora.strftime("%Y-%m-%d %H:%M:%S")

class Produto(Base):
    __tablename__ = "produtos_bazar_v3"  # Nova tabela com a regra de status

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    imagem_url = Column(String, nullable=True)
    estado_conservacao = Column(String, nullable=False)
    estoque = Column(Integer, default=1)
    status = Column(String, default="Disponivel")  # Disponivel, Reservado, Sold
    criado_em = Column(String, default=obter_hora_brasilia_str)
""")

# 4. Atualiza os Schemas de Produtos com o campo 'status'
with open("app/produtos/schemas.py", "w", encoding="utf-8") as f:
    f.write("""from pydantic import BaseModel
from typing import Optional

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    imagem_url: Optional[str] = None
    estado_conservacao: str
    estoque: int = 1
    status: Optional[str] = "Disponivel"

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    imagem_url: Optional[str] = None
    estado_conservacao: Optional[str] = None
    estoque: Optional[int] = None
    status: Optional[str] = None

class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: str

    class Config:
        from_attributes = True
""")

# 5. Atualiza as Rotas de Produtos com PUT, DELETE e filtros de Status
with open("app/produtos/rotas.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db, engine, Base
from app.produtos.modelos import Produto
from app.produtos.schemas import ProdutoCreate, ProdutoUpdate, ProdutoResponse

Base.metadata.create_all(bind=engine)

router = APIRouter()

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    # Traz todos os produtos salvos na tabela
    return db.query(Produto).all()

@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    novo_produto = Produto(**produto.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@router.put("/{produto_id}", response_model=ProdutoResponse)
def editar_produto(produto_id: int, dados: ProdutoUpdate, db: Session = Depends(get_db)):
    # Rota administrativa para atualizar preço, estoque, status, etc.
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    for chave, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, chave, valor)
        
    db.commit()
    db.refresh(produto)
    return produto

@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    # Rota administrativa para remover um item permanentemente
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    db.delete(produto)
    db.commit()
    return None
""")

# 6. Atualiza o main.py para incluir o novo módulo de usuários e tabelas
with open("app/main.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos.rotas import router as produtos_router
from app.usuarios.rotas import router as usuarios_router
from app.core.database import engine, Base

# Garante a criação de todas as tabelas (Produtos e Usuários)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bazar Online API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Liberado temporariamente para facilitar os testes do Front-end
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])
app.include_router(usuarios_router, prefix="/auth", tags=["Autenticação"])

@app.get("/")
def read_root():
    return {"status": "Backend do Bazar Online expandido e operando com sucesso!"}
""")

print("EXPANSÃO CONCLUÍDA! O módulo de Usuários, rotas PUT/DELETE e campos de Status foram injetados!")
