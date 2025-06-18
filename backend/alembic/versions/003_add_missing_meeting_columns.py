"""Add missing meeting columns

Revision ID: 003_add_missing_meeting_columns
Revises: 002_add_meeting_table
Create Date: 2025-06-18 22:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_missing_meeting_columns'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to meetings table
    op.add_column('meetings', sa.Column('status_details', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('meetings', sa.Column('speakers', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('meetings', sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove the columns if rolling back
    op.drop_column('meetings', 'status_details')
    op.drop_column('meetings', 'speakers')
    op.drop_column('meetings', 'error_details')
