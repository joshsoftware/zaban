"""add voiceprint tables

Revision ID: 20260212_01
Revises: 20251206_01
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql


# revision identifiers, used by Alembic.
revision = '20260212_01'
down_revision = '20251206_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop legacy table if exists
    op.execute("DROP TABLE IF EXISTS voiceprint_users CASCADE")

    # Create voiceprints table with all required columns
    op.create_table(
        'voiceprints',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('customer_id', sa.String(length=255), nullable=False),
        sa.Column('qdrant_vector_id', sa.BigInteger(), nullable=False),
        sa.Column('verification', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes and constraints for voiceprints table
    op.create_index('ix_voiceprints_qdrant_vector_id', 'voiceprints', ['qdrant_vector_id'], unique=True)
    # Unique constraint automatically creates a unique index, so no separate index needed
    op.create_unique_constraint('uq_voiceprints_customer_id', 'voiceprints', ['customer_id'])

    # Create verification_attempts table
    op.create_table(
        'verification_attempts',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('voiceprint_id', psql.UUID(as_uuid=True), sa.ForeignKey('voiceprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_plda_score', sa.Float(), nullable=False),
        sa.Column('as_norm_score', sa.Float(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes for verification_attempts table
    op.create_index('ix_verification_attempts_created_at', 'verification_attempts', ['created_at'], unique=False)
    op.create_index('ix_verification_attempts_voiceprint_id', 'verification_attempts', ['voiceprint_id'], unique=False)


def downgrade() -> None:
    # Drop verification_attempts table and its indexes
    op.drop_index('ix_verification_attempts_voiceprint_id', table_name='verification_attempts')
    op.drop_index('ix_verification_attempts_created_at', table_name='verification_attempts')
    op.drop_table('verification_attempts')
    
    # Drop voiceprints table and its indexes/constraints
    op.drop_constraint('uq_voiceprints_customer_id', 'voiceprints', type_='unique')
    op.drop_index('ix_voiceprints_qdrant_vector_id', table_name='voiceprints')
    op.drop_table('voiceprints')
