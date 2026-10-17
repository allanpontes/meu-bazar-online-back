"""baseline

Estado do schema em 2026-10-17 (develop/homolog), incluindo as colunas tamanho e categoria
que antes vinham de migrar_tamanho_categoria.py.

Em bancos que já têm essas tabelas (homolog, production) esta revisão NÃO é executada:
use `alembic stamp head`. Ela só roda de verdade num banco vazio (`alembic upgrade head`).

As tabelas antigas produtos, produtos_bazar e carrinho_reservas não fazem parte da baseline
(ver TABELAS_IGNORADAS em alembic/env.py); cada uma será apagada, se for o caso, numa revisão própria.

Revision ID: 1b97df6201c3
Revises:
Create Date: 2026-10-17 16:07:55.822417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1b97df6201c3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'produtos_bazar_v3',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=True),
        sa.Column('preco', sa.Float(), nullable=False),
        sa.Column('imagem_url', sa.String(), nullable=True),
        sa.Column('estado_conservacao', sa.String(), nullable=False),
        sa.Column('tamanho', sa.String(length=20), nullable=True),
        sa.Column('categoria', sa.String(length=30), nullable=True),
        sa.Column('estoque', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('criado_em', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_produtos_bazar_v3_id'), 'produtos_bazar_v3', ['id'], unique=False)

    op.create_table(
        'usuarios_bazar',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('senha_hash', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuarios_bazar_id'), 'usuarios_bazar', ['id'], unique=False)
    op.create_index(op.f('ix_usuarios_bazar_email'), 'usuarios_bazar', ['email'], unique=True)

    op.create_table(
        'pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome_cliente', sa.String(length=120), nullable=False),
        sa.Column('whatsapp', sa.String(length=20), nullable=False),
        sa.Column('endereco', sa.String(length=300), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pedidos_id'), 'pedidos', ['id'], unique=False)
    op.create_index(op.f('ix_pedidos_status'), 'pedidos', ['status'], unique=False)

    op.create_table(
        'sacola_itens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sessao_id', sa.String(length=36), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos_bazar_v3.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sacola_itens_id'), 'sacola_itens', ['id'], unique=False)
    op.create_index(op.f('ix_sacola_itens_sessao_id'), 'sacola_itens', ['sessao_id'], unique=False)
    op.create_index(op.f('ix_sacola_itens_produto_id'), 'sacola_itens', ['produto_id'], unique=False)
    op.create_index(
        'uq_sacola_produto_ativo',
        'sacola_itens',
        ['produto_id'],
        unique=True,
        postgresql_where=sa.text("status = 'Ativo'"),
    )

    op.create_table(
        'pedido_itens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=True),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('preco', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos_bazar_v3.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pedido_itens_id'), 'pedido_itens', ['id'], unique=False)
    op.create_index(op.f('ix_pedido_itens_pedido_id'), 'pedido_itens', ['pedido_id'], unique=False)


def downgrade() -> None:
    # A baseline é o ponto de partida: voltar daqui apagaria todos os dados (inclusive em production, onde ela só foi "stampada")
    raise RuntimeError("Não há downgrade da baseline: apagaria todas as tabelas.")
