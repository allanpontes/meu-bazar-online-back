from typing import List, Literal
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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origens_permitidas(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]

settings = Settings()
