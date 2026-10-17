from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.core.database import Base

# Os modelos precisam ser importados para entrar no Base.metadata (autogenerate e check)
from app.pedidos import modelos as _pedidos  # noqa: F401
from app.produtos import modelos as _produtos  # noqa: F401
from app.sacola import modelos as _sacola  # noqa: F401
from app.usuarios import modelos as _usuarios  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Tabelas antigas sem modelo (app/carrinho aposentado; produtos e produtos_bazar são de versões anteriores):
# o Alembic não pode tentar apagá-las. Remover cada uma só numa revisão própria, depois de conferir os dados.
TABELAS_IGNORADAS = {"carrinho_reservas", "produtos", "produtos_bazar"}


def incluir_objeto(objeto, nome, tipo, reflexo, comparado_com):
    if tipo == "table" and nome in TABELAS_IGNORADAS:
        return False
    return True


def run_migrations_offline() -> None:
    """Gera o SQL sem conectar ao banco (alembic upgrade head --sql)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=incluir_objeto,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # A URL vem de settings (variável de ambiente DATABASE_URL tem prioridade sobre o .env)
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=incluir_objeto,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
