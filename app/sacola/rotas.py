import uuid
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.sacola import servico
from app.sacola.schemas import SacolaResponse

router = APIRouter()

NOME_COOKIE = "sacola_sessao"
VALIDADE_COOKIE_SEGUNDOS = 24 * 60 * 60

def _sessao_valida(valor: Optional[str]) -> Optional[str]:
    # Só aceita UUID bem formado; qualquer outro valor é tratado como "sem sessão"
    try:
        return str(uuid.UUID(valor)) if valor else None
    except ValueError:
        return None

def _gravar_cookie(response: Response, sessao_id: str) -> None:
    response.set_cookie(
        key=NOME_COOKIE,
        value=sessao_id,
        max_age=VALIDADE_COOKIE_SEGUNDOS,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

@router.get("", response_model=SacolaResponse)
def ver_sacola(
    sacola_sessao: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    return servico.montar_sacola(db, _sessao_valida(sacola_sessao))

@router.post("/itens/{produto_id}", response_model=SacolaResponse)
def adicionar_item(
    produto_id: int,
    response: Response,
    sacola_sessao: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    sessao_id = _sessao_valida(sacola_sessao) or str(uuid.uuid4())
    servico.reservar(db, sessao_id, produto_id)
    _gravar_cookie(response, sessao_id)
    return servico.montar_sacola(db, sessao_id)

@router.delete("/itens/{produto_id}", response_model=SacolaResponse)
def remover_item(
    produto_id: int,
    sacola_sessao: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    sessao_id = _sessao_valida(sacola_sessao)
    if not sessao_id:
        return servico.montar_sacola(db, None)
    servico.remover(db, sessao_id, produto_id)
    return servico.montar_sacola(db, sessao_id)
