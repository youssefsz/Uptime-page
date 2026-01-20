"""initial_schema

Revision ID: 242aede75aae
Revises: 
Create Date: 2026-01-20 12:22:23.012609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '242aede75aae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create servers table
    op.create_table(
        'servers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create uptime_records table
    op.create_table(
        'uptime_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('UP', 'DOWN', name='statusenum'), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on server_id for faster lookups
    op.create_index('ix_uptime_records_server_id', 'uptime_records', ['server_id'], unique=False)
    op.create_index('ix_uptime_records_timestamp', 'uptime_records', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_uptime_records_timestamp', table_name='uptime_records')
    op.drop_index('ix_uptime_records_server_id', table_name='uptime_records')
    op.drop_table('uptime_records')
    op.drop_table('servers')
    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS statusenum')
