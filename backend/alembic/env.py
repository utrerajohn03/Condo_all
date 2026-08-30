"""
Alembic environment for the condo_ module.

Pulls the DB URL from app.config.settings (never hardcoded here — see alembic.ini),
and imports every model module so Base.metadata is fully populated for autogenerate.

Module-prefix note: the alembic_version bookkeeping table itself is named
condo_alembic_version (not the alembic default), so that — like every other table
this module owns — it carries the condo_ prefix and can't collide with another
intern's migration history when 25 modules are merged into one ARGO database.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# Import every model module so their tables attach to Base.metadata before
# Alembic reads it. The local stub (organizations/users) is imported too —
# needed so this module's FKs resolve in the sandbox, but its own migration
# is the only place that ever creates those two tables (see condo_zzz_local_stub).
from app.models import _local_stub_platform_tables  # noqa: F401
from app.models import condo_units  # noqa: F401
from app.models import condo_unit_residents  # noqa: F401
from app.models import condo_maintenance_requests  # noqa: F401
from app.models import condo_bills  # noqa: F401
from app.models import condo_payments  # noqa: F401
from app.models import condo_portal_settings  # noqa: F401

# this is the Alembic Config object, which provides access to values within
# the .ini file in use.
config = context.config

# Interpret the config file for Python logging, unless a section is missing
# (keeps `alembic` runnable even if someone trims alembic.ini's logging block).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Inject the real database URL from app settings (.env / DATABASE_URL) instead
# of reading it from alembic.ini, so there is exactly one place credentials live.
config.set_main_option("sqlalchemy.url", settings.database_url)

# condo_ prefix applied to Alembic's own bookkeeping table too — see module
# docstring above.
VERSION_TABLE = "condo_alembic_version"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL, no live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
