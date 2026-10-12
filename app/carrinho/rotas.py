from fastapi import APIRouter, Depends, HTTPException, status
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
