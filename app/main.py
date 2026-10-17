from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.produtos.rotas import router as produtos_router
from app.usuarios.rotas import router as usuarios_router
from app.dashboard.rotas import router as dashboard_router
from app.sacola.rotas import router as sacola_router
from app.pedidos.rotas import router as pedidos_router
from app.core.config import settings
from app.core.database import engine, Base

# Cria absolutamente todas as tabelas novas no Neon de uma vez só
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bazar Online API Super", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origens_permitidas,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(produtos_router, prefix="/produtos", tags=["Produtos"])
app.include_router(usuarios_router, prefix="/auth", tags=["Autenticação"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard Gerencial"])
app.include_router(sacola_router, prefix="/sacola", tags=["Sacola do Visitante"])
app.include_router(pedidos_router, prefix="/pedidos", tags=["Pedidos"])
@app.get("/")
def read_root():
    return {"status": "Backend do Bazar Online completo com Dashboard operando!"}
