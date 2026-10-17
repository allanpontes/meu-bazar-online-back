from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

StatusProduto = Literal["Disponivel", "Reservado", "Vendido"]
CategoriaProduto = Literal["Roupa", "Calçado", "Bolsa", "Acessório", "Outros"]

def validar_imagem_url(valor: Optional[str]) -> Optional[str]:
    # Só https com domínio; o campo sai quando as fotos passarem a ser enviadas por upload (ROADMAP 2.12)
    if valor is None or valor.strip() == "":
        return None
    valor = valor.strip()
    partes = urlparse(valor)
    if partes.scheme != "https" or not partes.netloc:
        raise ValueError("imagem_url deve ser um endereço https://")
    return valor

class ProdutoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    descricao: Optional[str] = None
    preco: float = Field(gt=0)
    imagem_url: Optional[str] = None
    estado_conservacao: str = Field(min_length=1, max_length=50)
    tamanho: Optional[str] = Field(default=None, max_length=20)
    categoria: Optional[CategoriaProduto] = None
    estoque: int = Field(default=1, ge=0)

class ProdutoCreate(ProdutoBase):
    # status não é aceito aqui: é controlado pelo fluxo de sacola e pedidos
    @field_validator("imagem_url")
    @classmethod
    def imagem_https(cls, v):
        return validar_imagem_url(v)

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=150)
    descricao: Optional[str] = None
    preco: Optional[float] = Field(default=None, gt=0)
    imagem_url: Optional[str] = None
    estado_conservacao: Optional[str] = Field(default=None, min_length=1, max_length=50)
    tamanho: Optional[str] = Field(default=None, max_length=20)
    categoria: Optional[CategoriaProduto] = None
    estoque: Optional[int] = Field(default=None, ge=0)

    @field_validator("imagem_url")
    @classmethod
    def imagem_https(cls, v):
        return validar_imagem_url(v)

class ProdutoResponse(ProdutoBase):
    id: int
    status: StatusProduto
    criado_em: str

    class Config:
        from_attributes = True
