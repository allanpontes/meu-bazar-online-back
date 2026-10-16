from sqlalchemy import Column, Integer, String, Float
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.database import Base

def obter_hora_brasilia_str():
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return agora.strftime("%Y-%m-%d %H:%M:%S")

class Produto(Base):
    __tablename__ = "produtos_bazar_v3"  # Nova tabela com a regra de status

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    imagem_url = Column(String, nullable=True)
    estado_conservacao = Column(String, nullable=False)
    tamanho = Column(String(20), nullable=True)
    categoria = Column(String(30), nullable=True)
    estoque = Column(Integer, default=1)
    status = Column(String, default="Disponivel")  # Disponivel, Reservado, Vendido
    criado_em = Column(String, default=obter_hora_brasilia_str)
