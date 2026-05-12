"""Async SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from cursor_metrics.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async_engine = create_async_engine(
    get_settings().DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields an async database session."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
