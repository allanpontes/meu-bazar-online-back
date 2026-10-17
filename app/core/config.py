import logging
from typing import List, Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("uvicorn.error")

class Settings(BaseSettings):
    DATABASE_URL: str
    # Origens do front separadas por vírgula; obrigatório ser explícito por causa dos cookies
    FRONTEND_ORIGINS: str = "http://localhost:4200"
    # Em produção com HTTPS: COOKIE_SECURE=true e, se front e API estiverem em domínios diferentes, COOKIE_SAMESITE=none
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SACOLA_MINUTOS: int = 15
    SACOLA_MAX_ITENS: int = 10
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
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SAMESITE=none exige COOKIE_SECURE=true, senão o navegador descarta o cookie")
        if self.COOKIE_SECURE and any("localhost" in o for o in self.origens_permitidas):
            logger.warning("FRONTEND_ORIGINS contém localhost com COOKIE_SECURE=true: confira se este ambiente é o publicado")
        return self

settings = Settings()
