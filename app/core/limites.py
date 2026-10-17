import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def ip_do_cliente(request: Request) -> str:
    # Atrás de proxy (Render) request.client é o proxy; o visitante vem em X-Forwarded-For.
    # Só confiamos nas últimas PROXY_SALTOS entradas, que os proxies nossos acrescentam; as da frente podem ser forjadas
    encaminhado = request.headers.get("x-forwarded-for")
    if settings.PROXY_SALTOS > 0 and encaminhado:
        ips = [ip.strip() for ip in encaminhado.split(",") if ip.strip()]
        if len(ips) >= settings.PROXY_SALTOS:
            return ips[-settings.PROXY_SALTOS]
    return request.client.host if request.client else "desconhecido"

limiter = Limiter(key_func=ip_do_cliente, enabled=settings.LIMITES_ATIVOS)

def limite_excedido(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    try:
        espera = int(exc.limit.limit.get_expiry())
    except AttributeError:
        espera = 60
    # Registra o IP escolhido e quantas entradas vieram, para conferir PROXY_SALTOS no deploy
    logger.warning(
        "limite excedido: %s %s ip=%s entradas_xff=%d",
        request.method, request.url.path, ip_do_cliente(request),
        len((request.headers.get("x-forwarded-for") or "").split(",")) if request.headers.get("x-forwarded-for") else 0,
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas tentativas. Aguarde um pouco e tente novamente."},
        headers={"Retry-After": str(espera)},
    )
