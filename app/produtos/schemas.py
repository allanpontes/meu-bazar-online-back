from pydantic import BaseModel, Field
from typing import Literal, Optional

StatusProduto = Literal["Disponivel", "Reservado", "Vendido"]

class ProdutoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    descricao: Optional[str] = None
    preco: float = Field(gt=0)
    imagem_url: Optional[str] = None
    estado_conservacao: str = Field(min_length=1, max_length=50)
    estoque: int = Field(default=1, ge=0)
    status: StatusProduto = "Disponivel"

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=150)
    descricao: Optional[str] = None
    preco: Optional[float] = Field(default=None, gt=0)
    imagem_url: Optional[str] = None
    estado_conservacao: Optional[str] = Field(default=None, min_length=1, max_length=50)
    estoque: Optional[int] = Field(default=None, ge=0)
    status: Optional[StatusProduto] = None

class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: str

    class Config:
        from_attributes = True
