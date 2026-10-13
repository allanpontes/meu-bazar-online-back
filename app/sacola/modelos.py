from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, text
from app.core.database import Base

def agora_utc() -> datetime:
    return datetime.now(timezone.utc)

class ItemSacola(Base):
    __tablename__ = "sacola_itens"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(String(36), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos_bazar_v3.id", ondelete="CASCADE"), nullable=False, index=True)
    criado_em = Column(DateTime(timezone=True), default=agora_utc, nullable=False)
    expira_em = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="Ativo", nullable=False)  # Ativo, Expirado, Removido, Comprado

    # Garante no banco que uma peça só tem um item ativo na sacola de alguém
    __table_args__ = (
        Index(
            "uq_sacola_produto_ativo",
            "produto_id",
            unique=True,
            postgresql_where=text("status = 'Ativo'"),
            sqlite_where=text("status = 'Ativo'"),
        ),
    )
