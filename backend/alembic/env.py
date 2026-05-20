import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No ORM models — raw SQL migrations only
target_metadata = None


def get_url():
    host     = os.getenv("DATABASE_HOST", "localhost")
    port     = os.getenv("DATABASE_PORT", "5432")
    dbname   = os.getenv("DATABASE_NAME", "reedintel")
    user     = os.getenv("DATABASE_USER", "reedadmin")
    password = os.getenv("DATABASE_PASSWORD", "")
    sslmode  = os.getenv("DATABASE_SSLMODE", "require")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"


def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
