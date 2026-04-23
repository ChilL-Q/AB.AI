"""
Test fixtures. Uses the Postgres configured via DATABASE_URL (in CI) or
the local default (for local runs). The schema is created fresh per test
session via SQLAlchemy metadata — alembic migrations are tested
separately. Each test runs inside a transaction that is rolled back,
keeping fixtures independent.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Importing the models package ensures every table is registered on Base.metadata
# before we call create_all.
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models.client import Client
from app.db.models.team import Team
from app.db.models.user import User


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    eng = create_async_engine(settings.database_url, echo=False, poolclass=None)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def team(session: AsyncSession) -> Team:
    t = Team(name="Test Service", slug=f"test-{uuid.uuid4().hex[:8]}")
    session.add(t)
    await session.flush()
    return t


@pytest_asyncio.fixture
async def user(session: AsyncSession, team: Team) -> User:
    u = User(
        email=f"owner-{uuid.uuid4().hex[:8]}@test.local",
        password_hash="x",
        full_name="Owner",
        team_id=team.id,
        role="owner",
    )
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
async def client(session: AsyncSession, team: Team) -> Client:
    c = Client(
        team_id=team.id,
        full_name="Иван Иванов",
        phone=f"+77{uuid.uuid4().int % 10**9:09d}",
    )
    session.add(c)
    await session.flush()
    return c
