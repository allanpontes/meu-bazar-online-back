from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db, engine, Base
from app.produtos.modelos import Produto
from app.produtos.schemas import ProdutoCreate, ProdutoUpdate, ProdutoResponse
from app.sacola.servico import liberar_expirados

Base.metadata.create_all(bind=engine)

router = APIRouter()

@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    # Devolve à vitrine as peças cujas reservas já venceram antes de listar
    liberar_expirados(db)
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
