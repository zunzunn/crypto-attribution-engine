"""Shared pytest fixtures.

Test DB selection:
  * If TEST_DATABASE_URL is set (PostgreSQL), a unique schema is created,
    migrated (create_all), and dropped afterwards.
  * Otherwise tests fall back to an in-memory SQLite engine (StaticPool) so
    the suite runs anywhere. PostgreSQL remains the recommended test target.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app.models  # noqa: F401  (register models on metadata)
from app.core.config import get_settings
from app.db.base import Base
from app.db.engine import AsyncSessionFactory, build_session_factory


def _test_database_url() -> str | None:
    raw = get_settings().test_database_url
    return raw.strip() if raw else None


@pytest.fixture
async def test_database_url() -> str | None:
    return _test_database_url()


@pytest.fixture
async def session_factory(test_database_url) -> AsyncSessionFactory:
    url = test_database_url or "sqlite+aiosqlite:///:memory:"
    factory = build_session_factory(url, echo=False)
    namespace: str | None = None

    if url.startswith("sqlite"):
        async with factory.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    else:
        namespace = f"test_{uuid.uuid4().hex[:10]}"
        async with factory.engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {namespace}"))
        scoped_engine = factory.engine.execution_options(schema_translate_map={None: namespace})
        factory = AsyncSessionFactory(
            engine=scoped_engine,
            maker=async_sessionmaker(scoped_engine, class_=AsyncSession, expire_on_commit=False),
        )
        async with scoped_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield factory

    if url.startswith("sqlite"):
        async with factory.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    else:
        async with factory.engine.begin() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {namespace} CASCADE"))
    await factory.dispose()


@pytest.fixture
async def session(session_factory) -> AsyncSession:
    async with session_factory() as s:
        yield s