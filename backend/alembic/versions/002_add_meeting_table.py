"""add meeting table

Revision ID: 002
Revises: 001
Create Date: 2025-01-14 00:49:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create meetings table
    op.create_table('meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.String(length=255), nullable=True),
        sa.Column('meeting_url', sa.String(length=500), nullable=True),
        sa.Column('bot_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('transcript', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('attendees', sa.JSON(), nullable=True),
        sa.Column('recording_url', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_bot_id'), 'meetings', ['bot_id'], unique=True)


def downgrade() -> None:
    # Drop meetings table
    op.drop_index(op.f('ix_meetings_bot_id'), table_name='meetings')
    op.drop_table('meetings')
