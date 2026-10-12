import os

# 1. Cria as novas pastas dos módulos
os.makedirs("app/carrinho", exist_ok=True)
os.makedirs("app/dashboard", exist_ok=True)

# 2. Configura o Módulo de Carrinho e Reservas Temporárias
with open("app/carrinho/__init__.py", "w", encoding="utf-8") as f: f.write("")

with open("app/carrinho/modelos.py", "w", encoding="utf-8") as f:
    f.write("""from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class ReservaCarrinho(Base):
    __tablename__ = "carrinho_reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios_bazar.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos_bazar_v3.id"), nullable=False)
    reservado_em = Column(DateTime, default=datetime.utcnow)
    status_reserva = Column(String, default="No Carrinho") # No Carrinho, Expirado, Comprado
""")

with open("app/carrinho/rotas.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.carrinho.modelos import ReservaCarrinho
from app.produtos.modelos import Produto

router = APIRouter()

@router.post("/adicionar/{usuario_id}/{produto_id}", status_code=status.HTTP_201_CREATED)
def adicionar_ao_carrinho(usuario_id: int, produto_id: int, db: Session = Depends(get_db)):
    # Verifica se o produto existe e está disponível
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    if produto.status != "Disponivel":
        raise HTTPException(status_code=400, detail="Este produto já está reservado ou vendido.")
    
    # Altera o status do produto para 'Reservado' para ninguém mais pegar
    produto.status = "Reservado"
    
    nova_reserva = ReservaCarrinho(usuario_id=usuario_id, produto_id=produto_id)
    db.add(nova_reserva)
    db.commit()
    return {"mensagem": "Produto reservado no seu carrinho por 15 minutos!"}
""")

# 3. Configura o Módulo de Dashboard e Volumetria para o Gerente
with open("app/dashboard/__init__.py", "w", encoding="utf-8") as f: f.write("")

with open("app/dashboard/rotas.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.produtos.modelos import Produto
from app.usuarios.modelos import Usuario

router = APIRouter()

@router.get("/resumo")
def obter_metricas_dashboard(db: Session = Depends(get_db)):
    # 1. Volumetria de Clientes/Usuários cadastrados
    total_usuarios = db.query(Usuario).count()
    
    # 2. Volumetria de Estoque total
    total_produtos = db.query(Produto).count()
    
    # 3. Faturamento Total (Soma o preço de tudo o que foi marcado como 'Vendido')
    faturamento = db.query(func.sum(Produto.preco)).filter(Produto.status == "Vendido").scalar() or 0.0
    
    # 4. Contagem por Status para o gráfico do Dashboard
    disponiveis = db.query(Produto).filter(Produto.status == "Disponivel").count()
    reservados = db.query(Produto).filter(Produto.status == "Reservado").count()
    vendidos = db.query(Produto).filter(Produto.status == "Vendido").count()
    
    return {
        "clientes_registrados": total_usuarios,
        "total_itens_historico": total_produtos,
        "faturamento_total_reais": round(faturamento, 2),
        "grafico_status": {
            "disponiveis": disponiveis,
            "reservados": reservados,
            "vendidos": vendidos
        }
    }
""")

# 4. Atualiza o arquivo principal app/main.py para engatar os novos módulos
with open("app/main.py", "w", encoding="utf-8") as f:
    f.write("""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos.rotas import router as produtos_router
from app.usuarios.rotas import router as usuarios_router
from app.carrinho.rotas import router as carrinho_router
from app.dashboard.rotas import router as dashboard_router
from app.core.database import engine, Base

# Cria absolutamente todas as tabelas novas no Neon de uma vez só
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bazar Online API Super", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])
app.include_router(usuarios_router, prefix="/auth", tags=["Autenticação"])
app.include_router(carrinho_router, prefix="/carrinho", tags=["Carrinho e Reservas"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard Gerencial"])

@app.get("/")
def read_root():
    return {"status": "Backend do Bazar Online completo com Dashboard e Carrinho operando!"}
""")

print("MÁGICA CONCLUÍDA! Módulos de Carrinho e Dashboard acoplados com sucesso absoluto!")
