import uuid
from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.limites import limiter
from app.sacola import servico
from app.sacola.schemas import SacolaResponse

router = APIRouter()

NOME_COOKIE = "sacola_sessao"
NOME_CABECALHO = "X-Sacola-Sessao"
VALIDADE_COOKIE_SEGUNDOS = 24 * 60 * 60

def _sessao_valida(valor: Optional[str]) -> Optional[str]:
    # Só aceita UUID bem formado; qualquer outro valor é tratado como "sem sessão"
    try:
        return str(uuid.UUID(valor)) if valor else None
    except ValueError:
        return None

def sessao_da_requisicao(
    sacola_sessao: Optional[str] = Cookie(default=None),
    x_sacola_sessao: Optional[str] = Header(default=None),
) -> Optional[str]:
    # O front guarda o id no localStorage e o manda no cabeçalho, porque o Safari bloqueia cookie entre sites.
    # O cookie continua valendo como segunda opção (ROADMAP 1.3: reavaliar quando houver domínio próprio)
    return _sessao_valida(x_sacola_sessao) or _sessao_valida(sacola_sessao)

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
    response: Response,
    sessao_id: Optional[str] = Depends(sessao_da_requisicao),
    db: Session = Depends(get_db),
):
    if sessao_id:
        response.headers[NOME_CABECALHO] = sessao_id
    return servico.montar_sacola(db, sessao_id)

@router.post("/itens/{produto_id}", response_model=SacolaResponse)
@limiter.limit(settings.LIMITE_SACOLA)
def adicionar_item(
    request: Request,
    produto_id: int,
    response: Response,
    sessao_existente: Optional[str] = Depends(sessao_da_requisicao),
    db: Session = Depends(get_db),
):
    sessao_id = sessao_existente or str(uuid.uuid4())
    servico.reservar(db, sessao_id, produto_id)
    _gravar_cookie(response, sessao_id)
    response.headers[NOME_CABECALHO] = sessao_id
    return servico.montar_sacola(db, sessao_id)

@router.delete("/itens/{produto_id}", response_model=SacolaResponse)
def remover_item(
    produto_id: int,
    response: Response,
    sessao_id: Optional[str] = Depends(sessao_da_requisicao),
    db: Session = Depends(get_db),
):
    if not sessao_id:
        return servico.montar_sacola(db, None)
    response.headers[NOME_CABECALHO] = sessao_id
    servico.remover(db, sessao_id, produto_id)
    return servico.montar_sacola(db, sessao_id)
