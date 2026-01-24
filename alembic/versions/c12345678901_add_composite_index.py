"""add_composite_index

Revision ID: c12345678901
Revises: b28fb3806145
Create Date: 2026-01-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c12345678901'
down_revision: Union[str, Sequence[str], None] = 'b28fb3806145'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create composite index
    op.create_index('ix_uptime_server_timestamp', 'uptime_records', ['server_id', 'timestamp'], unique=False)


def downgrade() -> None:
    # Drop composite index
    op.drop_index('ix_uptime_server_timestamp', table_name='uptime_records')
