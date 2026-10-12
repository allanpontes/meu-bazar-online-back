import os

estrutura = {
    "requirements.txt": """fastapi==0.110.0
uvicorn[standard]==0.28.0
sqlalchemy==2.0.28
psycopg2-binary==2.9.9
pydantic==2.6.4
pydantic-settings==2.2.1
python-dotenv==1.0.1
""",
    "app/__init__.py": "",
    "app/main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos.rotas import router as produtos_router

app = FastAPI(title="Bazar Online API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])

@app.get("/")
def read_root():
    return {"status": "Backend do Bazar Online está ativo e operando!"}
""",
    "app/core/__init__.py": "",
    "app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
""",
    "app/core/database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
    "app/produtos/__init__.py": "",
    "app/produtos/modelos.py": """from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    imagem_url = Column(String, nullable=True)
    estado_conservacao = Column(String, nullable=False)
    estoque = Column(Integer, default=1)
    criado_em = Column(DateTime, default=datetime.utcnow)
""",
    "app/produtos/schemas.py": """from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    imagem_url: Optional[str] = None
    estado_conservacao: str
    estoque: int = 1

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True
""",
    "app/produtos/rotas.py": """from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db, engine, Base
from app.produtos.modelos import Produto
from app.produtos.schemas import ProdutoCreate, ProdutoResponse

Base.metadata.create_all(bind=engine)

router = APIRouter()

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    produtos = db.query(Produto).all()
    return produtos

@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    # TODO: Implementar a dependência de segurança para Administradores aqui futuramente
    novo_produto = Produto(**produto.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto
"""
}

for caminho, conteudo in estrutura.items():
    diretorio = os.path.dirname(caminho)
    if diretorio and not os.path.exists(diretorio):
        os.makedirs(diretorio)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

print("MÁGICA CONCLUÍDA! Toda a estrutura e códigos do seu back-end foram criados com sucesso.")
