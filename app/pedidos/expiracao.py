from datetime import timedelta
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.core.config import settings
from app.pedidos.modelos import ItemPedido, Pedido
from app.produtos.modelos import Produto
from app.sacola.modelos import agora_utc

def expirar_pedidos_vencidos(db: Session) -> None:
    limite = agora_utc() - timedelta(hours=settings.PEDIDO_HORAS_PAGAMENTO)
    vencidos = [
        id_
        for (id_,) in db.query(Pedido.id)
        .filter(Pedido.status == "AguardandoPagamento", Pedido.criado_em <= limite)
        .all()
    ]
    for pedido_id in vencidos:
        # UPDATE condicional: se o admin marcou Pago/Cancelado agora, este pedido é ignorado
        marcado = db.execute(
            update(Pedido)
            .where(Pedido.id == pedido_id, Pedido.status == "AguardandoPagamento")
            .values(status="Expirado")
        )
        if marcado.rowcount != 1:
            continue
        ids = [
            produto_id
            for (produto_id,) in db.query(ItemPedido.produto_id)
            .filter(ItemPedido.pedido_id == pedido_id, ItemPedido.produto_id.isnot(None))
            .all()
        ]
        if ids:
            db.execute(
                update(Produto)
                .where(Produto.id.in_(ids), Produto.status == "Reservado")
                .values(status="Disponivel")
            )
    if vencidos:
        db.commit()
