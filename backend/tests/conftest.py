"""
Test configuration using testcontainers (PostgreSQL 16).
SQLite is forbidden — models use JSONB, UUID, TEXT[] (PostgreSQL-only types).

When TEST_DATABASE_URL env var is set (e.g. inside Docker Compose), the
existing postgres service is used directly — testcontainers is skipped.
"""
import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
_BACKEND_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def postgres_container():
    if _TEST_DATABASE_URL:
        yield None
        return
    from testcontainers.postgres import PostgresContainer
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container):
    if _TEST_DATABASE_URL:
        return _TEST_DATABASE_URL
    url = postgres_container.get_connection_url()
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session", autouse=True)
def run_migrations(postgres_container, db_url):
    """Run Alembic migrations against the test DB once per session.

    alembic/env.py reads TEST_DATABASE_URL directly, so subprocess call
    picks it up without needing psycopg2 as a separate dependency.
    """
    env = {**os.environ, "TEST_DATABASE_URL": db_url}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=_BACKEND_ROOT,
        env=env,
    )


@pytest.fixture(scope="session")
async def _engine(db_url) -> AsyncGenerator[AsyncEngine, None]:
    """Single engine shared across the test session — avoids pool creation overhead per test."""
    engine = create_async_engine(db_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test session isolated via transaction rollback."""
    factory = async_sessionmaker(_engine, expire_on_commit=False)
    async with factory() as sess:
        async with sess.begin():
            yield sess
            await sess.rollback()
