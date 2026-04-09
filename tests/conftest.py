"""Общие фикстуры интеграционных тестов."""

from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dimatech.core.config import Settings
from dimatech.core.security import hash_password
from dimatech.db.base import Base
from dimatech.db.models import Account, User, UserRole
from dimatech.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
	"""Возвращает настройки приложения для тестов."""
	database_path = tmp_path / 'test.db'
	return Settings(
		debug=True,
		database_url=f'sqlite+aiosqlite:///{database_path}',
		database_url_sync=f'sqlite:///{database_path}',
		jwt_secret_key='test-jwt-secret-key-for-suite-123456',
		jwt_algorithm='HS256',
		access_token_expire_minutes=60,
		payment_signature_secret='test-payment-secret',
		cache_ttl_seconds=60,
		cache_max_size=128,
	)


@pytest_asyncio.fixture
async def app(test_settings: Settings) -> AsyncIterator[FastAPI]:
	"""Создает приложение с SQLite."""
	database_engine = create_async_engine(url=test_settings.database_url)
	session_factory = async_sessionmaker(
		bind=database_engine,
		autoflush=False,
		expire_on_commit=False,
	)

	async with database_engine.begin() as connection:
		await connection.run_sync(Base.metadata.create_all)

	async with session_factory() as session:
		user = User(
			id=1,
			email='user@example.com',
			full_name='Тестовый пользователь',
			password_hash=hash_password(password='user12345'),
			role=UserRole.USER,
			is_active=True,
		)
		admin = User(
			id=2,
			email='admin@example.com',
			full_name='Тестовый администратор',
			password_hash=hash_password(password='admin12345'),
			role=UserRole.ADMIN,
			is_active=True,
		)
		session.add_all([user, admin])
		await session.flush()
		session.add(Account(id=1, user_id=user.id, balance=Decimal('1000.00')))
		await session.commit()

	try:
		yield create_app(settings=test_settings)
	finally:
		await database_engine.dispose()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
	"""Создает HTTP-клиент для тестирования API."""
	async with LifespanManager(app):
		transport = ASGITransport(app=app)
		async with AsyncClient(
			transport=transport, base_url='http://testserver'
		) as api_client:
			yield api_client
