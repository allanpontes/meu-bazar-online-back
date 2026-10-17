"""OBSOLETO: o schema agora é versionado pelo Alembic (pasta alembic/); a baseline já inclui estas colunas.
Mantido só como referência histórica até a branch production passar no alembic check.

Adiciona as colunas tamanho e categoria na tabela de produtos.

Uso, na raiz do back com o venv ativo:  python migrar_tamanho_categoria.py
Usa a DATABASE_URL do ambiente (ou do .env). Pode ser executado mais de uma vez.
"""
from sqlalchemy import text

from app.core.database import engine

COMANDOS = [
    "ALTER TABLE produtos_bazar_v3 ADD COLUMN IF NOT EXISTS tamanho VARCHAR(20)",
    "ALTER TABLE produtos_bazar_v3 ADD COLUMN IF NOT EXISTS categoria VARCHAR(30)",
]


def main() -> None:
    with engine.begin() as conexao:
        for comando in COMANDOS:
            conexao.execute(text(comando))
    print(f"Migracao concluida em: {engine.url.host}")


if __name__ == "__main__":
    main()
