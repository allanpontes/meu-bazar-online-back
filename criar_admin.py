"""Cria (ou redefine a senha de) um administrador.

Uso, na raiz do back com o venv ativo:  python criar_admin.py
A senha é pedida no terminal e nunca fica salva em arquivo nem no histórico.
"""
import getpass
import sys

from pydantic import TypeAdapter, ValidationError
from pydantic.networks import EmailStr

from app.core.database import Base, SessionLocal, engine
from app.core.seguranca import gerar_hash_senha
from app.usuarios.modelos import Usuario


def main() -> int:
    Base.metadata.create_all(bind=engine, tables=[Usuario.__table__])

    email_digitado = input("E-mail do admin: ").strip().lower()
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email_digitado))
    except ValidationError:
        print("E-mail inválido.")
        return 1

    senha = getpass.getpass("Senha (8 a 72 caracteres): ")
    if getpass.getpass("Repita a senha: ") != senha:
        print("As senhas não conferem.")
        return 1
    if not 8 <= len(senha.encode("utf-8")) <= 72:
        print("A senha precisa ter de 8 a 72 caracteres.")
        return 1

    with SessionLocal() as db:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario:
            usuario.senha_hash = gerar_hash_senha(senha)
            usuario.is_admin = True
            acao = "atualizado"
        else:
            db.add(Usuario(email=email, senha_hash=gerar_hash_senha(senha), is_admin=True))
            acao = "criado"
        db.commit()

    print(f"Admin {acao}: {email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
