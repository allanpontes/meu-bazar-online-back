from pydantic import BaseModel, EmailStr, Field

class UsuarioBase(BaseModel):
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=8, max_length=72)

class UsuarioResponse(UsuarioBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    senha: str
