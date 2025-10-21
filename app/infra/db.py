"""Database engine, session, and Alembic integration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class DatabaseManager:
    """Database connection manager with Alembic integration."""

    def __init__(self, database_url: str):
        """
        Initialize database manager.

        Args:
            database_url: PostgreSQL connection string (asyncpg format)
        """
        self.database_url = database_url
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Usage:
            async with db_manager.session() as session:
                result = await session.execute(select(User))
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def run_migrations(self) -> None:
        """
        Run Alembic migrations to upgrade database to the latest version.

        This is called during application startup to ensure the database
        schema is up to date.
        """
        logger.info("Running database migrations")

        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        alembic_ini_path = project_root / "alembic.ini"

        if not alembic_ini_path.exists():
            logger.warning(
                "alembic.ini not found, skipping migrations",
                path=str(alembic_ini_path),
            )
            return

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))

        # Override sqlalchemy.url with our database URL
        # Convert asyncpg:// to postgresql:// for Alembic (sync driver for migrations)
        sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

        try:
            # Run migrations synchronously (Alembic doesn't support async upgrades yet)
            # We run this in a thread pool to avoid blocking the event loop
            import asyncio

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error("Failed to run migrations", error=str(e), exc_info=True)
            raise

    async def close(self) -> None:
        """Close database connections."""
        logger.info("Closing database connections")
        await self.engine.dispose()
        logger.info("Database connections closed")


def init_db(database_url: str) -> DatabaseManager:
    """
    Initialize database connection and return manager.

    Args:
        database_url: PostgreSQL connection string (asyncpg format)

    Returns:
        DatabaseManager instance
    """
    logger.info("Initializing database manager", url=database_url.split("@")[-1])
    return DatabaseManager(database_url)
