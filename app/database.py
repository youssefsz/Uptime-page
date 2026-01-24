"""Database configuration and session management."""

import logging
import subprocess
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=20,  # Increased from 5
    max_overflow=20,  # Increased from 10
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database by running Alembic migrations.
    
    This ensures the database schema is managed exclusively through 
    Alembic migrations, providing proper version control and rollback support.
    """
    # Get the project root directory (where alembic.ini is located)
    project_root = Path(__file__).resolve().parent.parent
    
    try:
        logger.info("Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            logger.info(f"Alembic output: {result.stdout}")
        logger.info("Database migrations completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Alembic migration failed: {e.stderr}")
        raise RuntimeError(f"Database migration failed: {e.stderr}") from e
    except FileNotFoundError:
        logger.error("Alembic command not found. Make sure alembic is installed.")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
