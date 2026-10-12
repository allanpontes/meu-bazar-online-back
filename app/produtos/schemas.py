from pydantic import BaseModel
from typing import Optional

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    imagem_url: Optional[str] = None
    estado_conservacao: str
    estoque: int = 1
    status: Optional[str] = "Disponivel"

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    imagem_url: Optional[str] = None
    estado_conservacao: Optional[str] = None
    estoque: Optional[int] = None
    status: Optional[str] = None

class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: str

    class Config:
        from_attributes = True
