from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import Settings

logger = logging.getLogger(__name__)


def _to_asyncpg_url(settings: Settings) -> str:
    """Convert POSTGRES_URL into an async SQLAlchemy URL if needed.

    In many deployments POSTGRES_URL is already a full URL.
    We only ensure it uses the `postgresql+asyncpg://` dialect prefix.

    Contract:
      - Input: settings.postgres_url like "postgresql://user:pass@host:port/db"
      - Output: url with "postgresql+asyncpg://" prefix.
    """
    url = settings.postgres_url.strip()
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    # Fallback: best effort - do not mutate unknown schemes.
    return url


# PUBLIC_INTERFACE
def create_engine_and_sessionmaker(settings: Settings) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create the SQLAlchemy AsyncEngine and sessionmaker.

    Returns:
      (engine, sessionmaker)

    Errors:
      - Raises exceptions from SQLAlchemy engine creation on invalid URLs.
    """
    engine = create_async_engine(
        _to_asyncpg_url(settings),
        pool_pre_ping=True,
        future=True,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_maker


# PUBLIC_INTERFACE
async def get_db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession."""
    async with session_maker() as session:
        yield session
