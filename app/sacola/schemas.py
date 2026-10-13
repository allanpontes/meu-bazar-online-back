from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class ItemSacolaResponse(BaseModel):
    produto_id: int
    nome: str
    preco: float
    imagem_url: Optional[str] = None
    estado_conservacao: str
    expira_em: datetime
    segundos_restantes: int

class SacolaResponse(BaseModel):
    itens: List[ItemSacolaResponse]
    total_itens: int
    subtotal: float
