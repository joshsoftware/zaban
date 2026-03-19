from logging.config import fileConfig
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.db.database import Base
from app.models.user import User  # ensure model is imported
from app.models.password_reset_token import PasswordResetToken  # ensure model is imported
from app.models.voiceprint import Voiceprint, VerificationAttempt  # ensure model is imported

# Load environment variables from .env file
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def make_sync_url(url: str) -> str:
    """Convert async driver URL to sync for Alembic migrations.

    asyncpg cannot be used with synchronous SQLAlchemy engines.
    Alembic always runs migrations synchronously.
    """
    return (
        url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
           .replace("postgres+asyncpg://", "postgresql+psycopg://")
           .replace("postgres://", "postgresql+psycopg://")
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    raw_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    url = make_sync_url(raw_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    ini_section = config.get_section(config.config_ini_section, {})
    raw_url = os.getenv("DATABASE_URL") or ini_section.get("sqlalchemy.url")
    if raw_url:
        ini_section["sqlalchemy.url"] = make_sync_url(raw_url)

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
