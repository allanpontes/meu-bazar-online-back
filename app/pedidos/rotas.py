from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.limites import limiter
from app.core.seguranca import exigir_admin
from app.pedidos import servico
from app.pedidos.schemas import PedidoCreate, PedidoResponse, PedidoStatusUpdate, StatusPedido
from app.sacola.rotas import sessao_da_requisicao

router = APIRouter()

@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.LIMITE_PEDIDOS)
def criar_pedido(
    request: Request,
    dados: PedidoCreate,
    sessao_id: Optional[str] = Depends(sessao_da_requisicao),
    db: Session = Depends(get_db),
):
    return servico.criar_pedido(db, sessao_id, dados)

@router.get("", response_model=List[PedidoResponse], dependencies=[Depends(exigir_admin)])
def listar_pedidos(status_pedido: Optional[StatusPedido] = None, db: Session = Depends(get_db)):
    return servico.listar_pedidos(db, status_pedido)

@router.get("/{pedido_id}", response_model=PedidoResponse, dependencies=[Depends(exigir_admin)])
def ver_pedido(pedido_id: int, db: Session = Depends(get_db)):
    return servico.obter_pedido(db, pedido_id)

@router.put("/{pedido_id}/status", response_model=PedidoResponse, dependencies=[Depends(exigir_admin)])
def atualizar_status(pedido_id: int, dados: PedidoStatusUpdate, db: Session = Depends(get_db)):
    return servico.atualizar_status(db, pedido_id, dados.status)
