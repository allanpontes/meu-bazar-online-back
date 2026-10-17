from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload
from app.produtos.modelos import Produto
from app.sacola.modelos import ItemSacola
from app.sacola.servico import liberar_expirados
from app.pedidos.modelos import ItemPedido, Pedido
from app.pedidos.schemas import PedidoCreate

TRANSICOES = {
    "AguardandoPagamento": {"Pago", "Cancelado"},
    "Pago": {"Cancelado"},
    "Cancelado": set(),
    # Só se todas as peças ainda estiverem Disponivel (ver atualizar_status)
    "Expirado": {"Pago"},
}

def criar_pedido(db: Session, sessao_id: str | None, dados: PedidoCreate) -> Pedido:
    if not sessao_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sua sacola está vazia.")

    liberar_expirados(db)
    linhas = (
        db.query(ItemSacola, Produto)
        .join(Produto, Produto.id == ItemSacola.produto_id)
        .filter(ItemSacola.sessao_id == sessao_id, ItemSacola.status == "Ativo")
        .order_by(ItemSacola.criado_em)
        .all()
    )
    if not linhas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sua sacola está vazia ou as reservas expiraram.",
        )

    # Só uma requisição consegue converter os itens ativos em comprados
    ids = [item.id for item, _ in linhas]
    convertidos = db.execute(
        update(ItemSacola)
        .where(ItemSacola.id.in_(ids), ItemSacola.status == "Ativo")
        .values(status="Comprado")
    )
    if convertidos.rowcount != len(ids):
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sua sacola mudou. Revise os itens e tente novamente.")

    pedido = Pedido(
        nome_cliente=dados.nome_cliente,
        whatsapp=dados.whatsapp,
        endereco=dados.endereco,
        subtotal=round(sum(p.preco for _, p in linhas), 2),
        itens=[ItemPedido(produto_id=p.id, nome=p.nome, preco=p.preco) for _, p in linhas],
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido

def listar_pedidos(db: Session, filtro_status: Optional[str]) -> List[Pedido]:
    liberar_expirados(db)
    consulta = db.query(Pedido).options(selectinload(Pedido.itens))
    if filtro_status:
        consulta = consulta.filter(Pedido.status == filtro_status)
    return consulta.order_by(Pedido.criado_em.desc()).all()

def obter_pedido(db: Session, pedido_id: int) -> Pedido:
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")
    return pedido

def atualizar_status(db: Session, pedido_id: int, novo_status: str) -> Pedido:
    liberar_expirados(db)
    pedido = obter_pedido(db, pedido_id)
    status_anterior = pedido.status
    if novo_status not in TRANSICOES[status_anterior]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível mudar o pedido de {status_anterior} para {novo_status}.",
        )

    ids = [i.produto_id for i in pedido.itens if i.produto_id is not None]
    if status_anterior == "Expirado":
        # As peças foram devolvidas à vitrine: só reaproveita o pedido se nenhuma foi reservada ou vendida desde então
        vendidas = db.execute(
            update(Produto).where(Produto.id.in_(ids), Produto.status == "Disponivel").values(status="Vendido")
        ) if ids else None
        if len(ids) != len(pedido.itens) or vendidas is None or vendidas.rowcount != len(ids):
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este pedido expirou e alguma peça já não está disponível (foi reservada, vendida ou excluída). Não é possível marcá-lo como pago.",
            )
    elif ids:
        if novo_status == "Pago":
            db.execute(update(Produto).where(Produto.id.in_(ids), Produto.status == "Reservado").values(status="Vendido"))
        else:
            db.execute(
                update(Produto)
                .where(Produto.id.in_(ids), Produto.status.in_(["Reservado", "Vendido"]))
                .values(status="Disponivel")
            )
    # UPDATE condicional: se outra requisição mudou o pedido no meio do caminho, não sobrescreve
    mudou = db.execute(
        update(Pedido).where(Pedido.id == pedido_id, Pedido.status == status_anterior).values(status=novo_status)
    )
    if mudou.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="O pedido mudou enquanto você o atualizava. Recarregue e tente novamente.")
    db.commit()
    db.refresh(pedido)
    return pedido
