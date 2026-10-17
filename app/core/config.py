import logging
from typing import List, Literal, Optional
from limits import parse_many
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("uvicorn.error")

class Settings(BaseSettings):
    DATABASE_URL: str
    # Conexão direta (host sem -pooler) usada só pelo Alembic; se vazia, o Alembic usa DATABASE_URL
    DATABASE_URL_MIGRACAO: Optional[str] = None
    # Origens do front separadas por vírgula; obrigatório ser explícito por causa dos cookies
    FRONTEND_ORIGINS: str = "http://localhost:4200"
    # Em produção com HTTPS: COOKIE_SECURE=true e, se front e API estiverem em domínios diferentes, COOKIE_SAMESITE=none
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    # /docs, /redoc e /openapi.json; desligado por padrão, ligue só em local e develop
    DOCS_ATIVOS: bool = False
    # Limite de requisições por IP, no formato da biblioteca limits ("5/minute;20/hour").
    # Operadoras móveis compartilham IP entre clientes: ajuste aqui, sem mexer no código
    LIMITES_ATIVOS: bool = True
    LIMITE_LOGIN: str = "5/minute;20/hour"
    LIMITE_SACOLA: str = "10/minute;30/hour"
    LIMITE_PEDIDOS: str = "3/minute;10/hour"
    # Proxies confiáveis na frente da API: o IP do visitante é a N-ésima entrada de trás para frente em X-Forwarded-For.
    # Render: 3 (visitante, borda da Cloudflare, proxy interno do Render). 0 = ignora o cabeçalho (acesso direto, sem proxy)
    PROXY_SALTOS: int = Field(default=3, ge=0)
    SACOLA_MINUTOS: int = 15
    SACOLA_MAX_ITENS: int = 10
    # Prazo para combinar o pagamento: depois disso o pedido AguardandoPagamento vira Expirado e as peças voltam à vitrine
    PEDIDO_HORAS_PAGAMENTO: int = Field(default=12, gt=0)
    # Segredo que assina os JWT; sem valor padrão de propósito: o app não sobe sem ele
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITMO: str = "HS256"
    JWT_EXPIRA_MINUTOS: int = 480

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origens_permitidas(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def validar_configuracao(self):
        for origem in self.origens_permitidas:
            if origem == "*":
                raise ValueError("FRONTEND_ORIGINS não pode ser '*': com cookies as origens precisam ser explícitas")
            if origem.endswith("/"):
                raise ValueError(f"FRONTEND_ORIGINS não pode terminar com barra: '{origem}'")
        for nome in ("LIMITE_LOGIN", "LIMITE_SACOLA", "LIMITE_PEDIDOS"):
            try:
                parse_many(getattr(self, nome))
            except ValueError as erro:
                raise ValueError(f"{nome} inválido ({erro}); use por exemplo '5/minute;20/hour'")
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SAMESITE=none exige COOKIE_SECURE=true, senão o navegador descarta o cookie")
        if self.COOKIE_SECURE and any("localhost" in o for o in self.origens_permitidas):
            logger.warning("FRONTEND_ORIGINS contém localhost com COOKIE_SECURE=true: confira se este ambiente é o publicado")
        return self

settings = Settings()
