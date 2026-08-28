"""Async SQLAlchemy engine + session factory.

``AsyncSessionFactory`` wraps an engine and an ``async_sessionmaker`` so call
sites (FastAPI app factory, test fixture) can reach the engine (for lifecycle
management / schema creation) and make sessions without touching SQLAlchemy
internals.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool


def build_async_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine.

    PostgreSQL is the primary target. In-memory SQLite is supported for unit
    tests (single-connection StaticPool) so persistence/idempotency logic can
    run anywhere; the recommended CI/test target remains PostgreSQL.
    """
    kwargs: dict = {"pool_pre_ping": True, "echo": echo}
    if database_url.startswith("sqlite"):
        kwargs["poolclass"] = StaticPool
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_async_engine(database_url, **kwargs)


@dataclass
class AsyncSessionFactory:
    engine: AsyncEngine
    maker: async_sessionmaker[AsyncSession]

    def __call__(self, **kwargs: object) -> AsyncSession:
        return self.maker(**kwargs)

    async def dispose(self) -> None:
        await self.engine.dispose()

    @classmethod
    def build(cls, database_url: str, *, echo: bool = False) -> AsyncSessionFactory:
        engine = build_async_engine(database_url, echo=echo)
        maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return cls(engine=engine, maker=maker)


def build_session_factory(database_url: str, *, echo: bool = False) -> AsyncSessionFactory:
    return AsyncSessionFactory.build(database_url, echo=echo)