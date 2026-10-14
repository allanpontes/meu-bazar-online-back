from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    # Origens do front separadas por vírgula; obrigatório ser explícito por causa dos cookies
    FRONTEND_ORIGINS: str = "http://localhost:4200"
    # Em produção com HTTPS: COOKIE_SECURE=true e, se front e API estiverem em domínios diferentes, COOKIE_SAMESITE=none
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SACOLA_MINUTOS: int = 15
    SACOLA_MAX_ITENS: int = 10
    # Chave das rotas administrativas de pedidos; vazia = rotas bloqueadas
    ADMIN_API_KEY: str = ""
    # Segredo que assina os JWT; sem valor padrão de propósito: o app não sobe sem ele
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITMO: str = "HS256"
    JWT_EXPIRA_MINUTOS: int = 480

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origens_permitidas(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]

settings = Settings()
