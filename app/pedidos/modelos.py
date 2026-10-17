from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.sacola.modelos import agora_utc

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    nome_cliente = Column(String(120), nullable=False)
    whatsapp = Column(String(20), nullable=False)
    endereco = Column(String(300), nullable=False)
    subtotal = Column(Float, nullable=False)
    status = Column(String(20), default="AguardandoPagamento", nullable=False, index=True)  # AguardandoPagamento, Pago, Cancelado, Expirado
    criado_em = Column(DateTime(timezone=True), default=agora_utc, nullable=False)

    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan", order_by="ItemPedido.id")

class ItemPedido(Base):
    __tablename__ = "pedido_itens"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    # Nome e preço são copiados para o histórico do pedido não mudar se a peça for editada ou excluída
    produto_id = Column(Integer, ForeignKey("produtos_bazar_v3.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
