from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.seguranca import exigir_admin
from app.pedidos import servico
from app.pedidos.schemas import PedidoCreate, PedidoResponse, PedidoStatusUpdate, StatusPedido
from app.sacola.rotas import _sessao_valida

router = APIRouter()

@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    dados: PedidoCreate,
    sacola_sessao: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    return servico.criar_pedido(db, _sessao_valida(sacola_sessao), dados)

@router.get("", response_model=List[PedidoResponse], dependencies=[Depends(exigir_admin)])
def listar_pedidos(status_pedido: Optional[StatusPedido] = None, db: Session = Depends(get_db)):
    return servico.listar_pedidos(db, status_pedido)

@router.get("/{pedido_id}", response_model=PedidoResponse, dependencies=[Depends(exigir_admin)])
def ver_pedido(pedido_id: int, db: Session = Depends(get_db)):
    return servico.obter_pedido(db, pedido_id)

@router.put("/{pedido_id}/status", response_model=PedidoResponse, dependencies=[Depends(exigir_admin)])
def atualizar_status(pedido_id: int, dados: PedidoStatusUpdate, db: Session = Depends(get_db)):
    return servico.atualizar_status(db, pedido_id, dados.status)
