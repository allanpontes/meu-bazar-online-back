import re
from datetime import datetime, timedelta
from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from app.core.config import settings

StatusPedido = Literal["AguardandoPagamento", "Pago", "Cancelado", "Expirado"]

class PedidoCreate(BaseModel):
    nome_cliente: str = Field(min_length=2, max_length=120)
    whatsapp: str
    endereco: str = Field(min_length=5, max_length=300)

    @field_validator("nome_cliente", "endereco")
    @classmethod
    def _sem_espacos_nas_pontas(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("whatsapp")
    @classmethod
    def _somente_digitos(cls, valor: str) -> str:
        digitos = re.sub(r"\D", "", valor)
        if not 10 <= len(digitos) <= 13:
            raise ValueError("Informe um WhatsApp válido com DDD.")
        return digitos

class ItemPedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int | None
    nome: str
    preco: float

class PedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_cliente: str
    whatsapp: str
    endereco: str
    subtotal: float
    status: StatusPedido
    criado_em: datetime
    itens: List[ItemPedidoResponse]

    @computed_field
    @property
    def expira_em(self) -> datetime:
        return self.criado_em + timedelta(hours=settings.PEDIDO_HORAS_PAGAMENTO)

class PedidoStatusUpdate(BaseModel):
    status: Literal["Pago", "Cancelado"]
