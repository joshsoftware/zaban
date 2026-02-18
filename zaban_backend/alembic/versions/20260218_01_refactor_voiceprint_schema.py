"""refactor voiceprint schema

- Drop voiceprint_users table (if exists)
- Voiceprints: drop model_name, rename user_id -> customer_id,
  add unique constraint on customer_id, add verification and last_verified_at columns,
  drop FK to users, rebuild partial index
- VerificationAttempts: drop user_id, probe_qdrant_vector_id, decision columns,
  add count column, drop user_id index

Revision ID: 20260218_01
Revises: 20260212_01
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260218_01'
down_revision = '20260212_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── voiceprint_users: drop if it exists ──────────────────────────
    op.execute("""
        DROP TABLE IF EXISTS voiceprint_users CASCADE
    """)

    # ── voiceprints table changes ────────────────────────────────────

    # 1. Drop old partial index (references user_id)
    op.drop_index('idx_voiceprints_active', table_name='voiceprints')

    # 2. Drop FK constraint on user_id (to users.id)
    #    Convention name may vary; use raw SQL for safety
    op.execute("""
        ALTER TABLE voiceprints
        DROP CONSTRAINT IF EXISTS voiceprints_user_id_fkey
    """)

    # 3. Drop old user_id index
    op.drop_index('ix_voiceprints_user_id', table_name='voiceprints')

    # 4. Rename user_id -> customer_id
    op.alter_column('voiceprints', 'user_id', new_column_name='customer_id')

    # 5. Change customer_id type from UUID to String(255)
    op.alter_column(
        'voiceprints', 'customer_id',
        type_=sa.String(255),
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using='customer_id::text',
    )

    # 6. Change qdrant_vector_id type from UUID to BigInteger
    op.alter_column(
        'voiceprints', 'qdrant_vector_id',
        type_=sa.BigInteger(),
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using='0',  # reset to 0 since old UUIDs can't cast to bigint
    )

    # 7. Add unique constraint on customer_id (one voiceprint per customer)
    op.create_unique_constraint('uq_voiceprints_customer_id', 'voiceprints', ['customer_id'])

    # 8. Create new index on customer_id
    op.create_index('ix_voiceprints_customer_id', 'voiceprints', ['customer_id'], unique=False)

    # 9. Recreate partial index with customer_id
    op.create_index(
        'idx_voiceprints_active',
        'voiceprints',
        ['customer_id', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true'),
    )

    # 10. Drop model_name column
    op.drop_column('voiceprints', 'model_name')

    # 11. Add verification column (boolean, default false)
    op.add_column('voiceprints', sa.Column('verification', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # 12. Add last_verified_at column (nullable timestamp)
    op.add_column('voiceprints', sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True))

    # ── verification_attempts table changes ──────────────────────────

    # 1. Drop FK and index on user_id
    op.execute("""
        ALTER TABLE verification_attempts
        DROP CONSTRAINT IF EXISTS verification_attempts_user_id_fkey
    """)
    op.drop_index('ix_verification_attempts_user_id', table_name='verification_attempts')

    # 2. Drop columns: user_id, probe_qdrant_vector_id, decision
    op.drop_column('verification_attempts', 'user_id')
    op.drop_column('verification_attempts', 'probe_qdrant_vector_id')
    op.drop_column('verification_attempts', 'decision')

    # 3. Add count column (integer, default 0)
    op.add_column('verification_attempts', sa.Column('count', sa.Integer(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    # ── verification_attempts: revert ────────────────────────────────
    op.drop_column('verification_attempts', 'count')

    op.add_column('verification_attempts', sa.Column('decision', sa.String(20), nullable=False, server_default='unknown'))
    op.add_column('verification_attempts', sa.Column('probe_qdrant_vector_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('verification_attempts', sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    op.create_index('ix_verification_attempts_user_id', 'verification_attempts', ['user_id'], unique=False)

    # ── voiceprints: revert ──────────────────────────────────────────
    op.drop_column('voiceprints', 'last_verified_at')
    op.drop_column('voiceprints', 'verification')

    op.add_column('voiceprints', sa.Column('model_name', sa.String(100), nullable=False, server_default='ecapa-tdnn-voxceleb'))

    op.drop_index('idx_voiceprints_active', table_name='voiceprints')
    op.drop_index('ix_voiceprints_customer_id', table_name='voiceprints')
    op.drop_constraint('uq_voiceprints_customer_id', 'voiceprints', type_='unique')

    # Change qdrant_vector_id back to UUID
    op.alter_column(
        'voiceprints', 'qdrant_vector_id',
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_type=sa.BigInteger(),
        existing_nullable=False,
        postgresql_using='gen_random_uuid()',
    )

    # Change customer_id back to UUID
    op.alter_column(
        'voiceprints', 'customer_id',
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_type=sa.String(255),
        existing_nullable=False,
        postgresql_using='customer_id::uuid',
    )

    # Rename customer_id -> user_id
    op.alter_column('voiceprints', 'customer_id', new_column_name='user_id')

    op.create_index('ix_voiceprints_user_id', 'voiceprints', ['user_id'], unique=False)

    # Recreate FK to users.id
    op.create_foreign_key(
        'voiceprints_user_id_fkey',
        'voiceprints', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    # Recreate partial index with user_id
    op.create_index(
        'idx_voiceprints_active',
        'voiceprints',
        ['user_id', 'is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true'),
    )

    # Recreate FK on verification_attempts.user_id
    op.create_foreign_key(
        'verification_attempts_user_id_fkey',
        'verification_attempts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE',
    )
