import ipaddress
import logging
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def _normalizar(ip: Optional[str]) -> Optional[str]:
    # Devolve o IP como chave do limite; None se não for um endereço válido.
    # IPv6 vale pelo prefixo /64: uma operadora entrega faixas inteiras ao cliente, que giraria de endereço para burlar o limite
    try:
        endereco = ipaddress.ip_address((ip or "").strip())
    except ValueError:
        return None
    if endereco.version == 6:
        if endereco.ipv4_mapped:
            return str(endereco.ipv4_mapped)
        return str(ipaddress.ip_network(f"{endereco}/64", strict=False))
    return str(endereco)

def ip_do_cliente(request: Request) -> str:
    # Já calculado nesta requisição (cada limite chama a função de chave)
    guardado = getattr(request.state, "ip_cliente", None)
    if guardado:
        return guardado

    # Atrás de proxies, request.client não é o visitante; ele vem em X-Forwarded-For.
    # Cada proxy acrescenta à direita o IP de quem se conectou a ele, então só confiamos nas
    # últimas PROXY_SALTOS entradas: o que vem antes pode ser forjado pelo visitante.
    # No Render são 3: [visitante, borda da Cloudflare, proxy interno do Render]
    escolhido = None
    encaminhado = request.headers.get("x-forwarded-for")
    if settings.PROXY_SALTOS > 0 and encaminhado:
        ips = [ip.strip() for ip in encaminhado.split(",") if ip.strip()]
        if len(ips) >= settings.PROXY_SALTOS:
            escolhido = _normalizar(ips[-settings.PROXY_SALTOS])
    chave = escolhido or _normalizar(request.client.host if request.client else None) or "desconhecido"

    # Verificação cruzada, só para avisar: a Cloudflare define CF-Connecting-IP com o IP do visitante.
    # Se divergir da chave, o número de proxies mudou e PROXY_SALTOS precisa ser revisto
    cloudflare = _normalizar(request.headers.get("cf-connecting-ip"))
    if cloudflare and cloudflare != chave:
        logger.warning(
            "PROXY_SALTOS=%d provavelmente errado: chave=%s mas CF-Connecting-IP=%s (entradas em X-Forwarded-For: %d)",
            settings.PROXY_SALTOS, chave, cloudflare, len((encaminhado or "").split(",")),
        )

    request.state.ip_cliente = chave
    return chave

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
