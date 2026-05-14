"""add trim to vehicles

Revision ID: a3c1d8e2f4b7
Revises: fe2a9887841c
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3c1d8e2f4b7'
down_revision: Union[str, Sequence[str], None] = 'fe2a9887841c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vehicles', sa.Column('trim', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('vehicles', 'trim')