"""
Database session management and connection handling.

This module provides async database session management using SQLAlchemy.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.database.base import Base

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    poolclass=NullPool if settings.environment == "test" else None,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# For backwards compatibility (will be removed in future)
SessionLocal = async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    This creates all tables defined in the Base metadata.
    Use Alembic migrations in production instead.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.error(f"Failed to initialize database: {e}")
        # For SQLite, create directory if it doesn't exist
        if "sqlite" in str(settings.database_url).lower():
            db_path = str(settings.database_url).split("///")[-1]
            from pathlib import Path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            # Retry once
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise


async def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Only use in development/testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    """
    Close database connections.

    Call this during application shutdown.
    """
    await engine.dispose()
