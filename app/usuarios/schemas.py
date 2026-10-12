from pydantic import BaseModel, EmailStr

class UsuarioBase(BaseModel):
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    senha: str
