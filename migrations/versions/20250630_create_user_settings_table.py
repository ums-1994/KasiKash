"""
Migration: Create user_settings table
Generated: 2025-06-30
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('setting_key', sa.String(255), nullable=False),
        sa.Column('setting_value', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('user_settings')
