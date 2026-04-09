"""Настройка окружения Alembic."""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / 'src'

sys.path.append(str(SRC_DIR))

from dimatech.core.config import get_settings  # noqa: E402
from dimatech.db import models  # noqa: E402, F401
from dimatech.db.base import Base  # noqa: E402

config = context.config
settings = get_settings()
config.set_main_option('sqlalchemy.url', settings.database_url_sync)

if config.config_file_name is not None:
	fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
	"""Запускает миграции в offline-режиме."""
	url = config.get_main_option('sqlalchemy.url')
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={'paramstyle': 'named'},
		compare_type=True,
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online() -> None:
	"""Запускает миграции в online-режиме."""
	connectable = engine_from_config(
		configuration=config.get_section(config.config_ini_section, {}),
		prefix='sqlalchemy.',
		poolclass=pool.NullPool,
	)

	with connectable.connect() as connection:
		context.configure(
			connection=connection, target_metadata=target_metadata, compare_type=True
		)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
