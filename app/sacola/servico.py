from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.produtos.modelos import Produto
from app.sacola.modelos import ItemSacola, agora_utc
from app.sacola.schemas import ItemSacolaResponse, SacolaResponse

def _como_utc(momento: datetime) -> datetime:
    return momento if momento.tzinfo else momento.replace(tzinfo=timezone.utc)

def _liberar_produto(db: Session, produto_id: int) -> None:
    db.execute(
        update(Produto)
        .where(Produto.id == produto_id, Produto.status == "Reservado")
        .values(status="Disponivel")
    )

def liberar_expirados(db: Session) -> None:
    vencidos = (
        db.query(ItemSacola)
        .filter(ItemSacola.status == "Ativo", ItemSacola.expira_em <= agora_utc())
        .all()
    )
    if not vencidos:
        return
    for item in vencidos:
        item.status = "Expirado"
        _liberar_produto(db, item.produto_id)
    db.commit()

def _item_ativo(db: Session, sessao_id: str, produto_id: int):
    return (
        db.query(ItemSacola)
        .filter(
            ItemSacola.sessao_id == sessao_id,
            ItemSacola.produto_id == produto_id,
            ItemSacola.status == "Ativo",
        )
        .first()
    )

def reservar(db: Session, sessao_id: str, produto_id: int) -> None:
    liberar_expirados(db)

    if not db.get(Produto, produto_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    if _item_ativo(db, sessao_id, produto_id):
        return

    ativos = (
        db.query(ItemSacola)
        .filter(ItemSacola.sessao_id == sessao_id, ItemSacola.status == "Ativo")
        .count()
    )
    if ativos >= settings.SACOLA_MAX_ITENS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sua sacola já tem o máximo de {settings.SACOLA_MAX_ITENS} peças.",
        )

    # UPDATE condicional: só uma requisição consegue trocar Disponivel por Reservado
    reservado = db.execute(
        update(Produto)
        .where(Produto.id == produto_id, Produto.status == "Disponivel")
        .values(status="Reservado")
    )
    if reservado.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta peça já foi reservada ou vendida.")

    db.add(ItemSacola(
        sessao_id=sessao_id,
        produto_id=produto_id,
        expira_em=agora_utc() + timedelta(minutes=settings.SACOLA_MINUTOS),
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta peça já foi reservada ou vendida.")

def remover(db: Session, sessao_id: str, produto_id: int) -> None:
    item = _item_ativo(db, sessao_id, produto_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esta peça não está na sua sacola.")
    item.status = "Removido"
    _liberar_produto(db, produto_id)
    db.commit()

def montar_sacola(db: Session, sessao_id: str | None) -> SacolaResponse:
    if not sessao_id:
        return SacolaResponse(itens=[], total_itens=0, subtotal=0.0)

    liberar_expirados(db)
    agora = agora_utc()
    linhas = (
        db.query(ItemSacola, Produto)
        .join(Produto, Produto.id == ItemSacola.produto_id)
        .filter(ItemSacola.sessao_id == sessao_id, ItemSacola.status == "Ativo")
        .order_by(ItemSacola.criado_em)
        .all()
    )
    itens = [
        ItemSacolaResponse(
            produto_id=produto.id,
            nome=produto.nome,
            preco=produto.preco,
            imagem_url=produto.imagem_url,
            estado_conservacao=produto.estado_conservacao,
            expira_em=_como_utc(item.expira_em),
            segundos_restantes=max(0, int((_como_utc(item.expira_em) - agora).total_seconds())),
        )
        for item, produto in linhas
    ]
    return SacolaResponse(
        itens=itens,
        total_itens=len(itens),
        subtotal=round(sum(i.preco for i in itens), 2),
    )
