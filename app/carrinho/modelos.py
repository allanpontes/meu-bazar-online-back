from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from app.core.database import Base

class ReservaCarrinho(Base):
    __tablename__ = "carrinho_reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios_bazar.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos_bazar_v3.id"), nullable=False)
    reservado_em = Column(DateTime, default=datetime.utcnow)
    status_reserva = Column(String, default="No Carrinho") # No Carrinho, Expirado, Comprado
