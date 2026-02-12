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
    # Create voiceprints table
    op.create_table(
        'voiceprints',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', psql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('qdrant_vector_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_voiceprints_qdrant_vector_id', 'voiceprints', ['qdrant_vector_id'], unique=True)
    op.create_index('ix_voiceprints_user_id', 'voiceprints', ['user_id'], unique=False)
    op.create_index(
        'idx_voiceprints_active',
        'voiceprints',
        ['user_id', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # Create verification_attempts table
    op.create_table(
        'verification_attempts',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', psql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voiceprint_id', psql.UUID(as_uuid=True), sa.ForeignKey('voiceprints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('probe_qdrant_vector_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_plda_score', sa.Float(), nullable=False),
        sa.Column('as_norm_score', sa.Float(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_verification_attempts_created_at', 'verification_attempts', ['created_at'], unique=False)
    op.create_index('ix_verification_attempts_user_id', 'verification_attempts', ['user_id'], unique=False)
    op.create_index('ix_verification_attempts_voiceprint_id', 'verification_attempts', ['voiceprint_id'], unique=False)


def downgrade() -> None:
    op.drop_table('verification_attempts')
    op.drop_table('voiceprints')
