"""
Test configuration using testcontainers (PostgreSQL 16).
SQLite is forbidden — models use JSONB, UUID, TEXT[] (PostgreSQL-only types).
"""
import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container):
    url = postgres_container.get_connection_url()
    # Replace psycopg2 scheme with asyncpg
    return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")


@pytest.fixture(scope="session", autouse=True)
def run_migrations(postgres_container, db_url):
    """Run Alembic migrations against the test container once per session."""
    alembic_cfg = Config("alembic.ini")
    # Use sync URL for Alembic (it handles async internally via env.py)
    sync_url = db_url.replace("+asyncpg", "+psycopg2")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def session(db_url) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test session isolated via transaction rollback."""
    engine = create_async_engine(db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        async with sess.begin():
            yield sess
            await sess.rollback()
    await engine.dispose()
