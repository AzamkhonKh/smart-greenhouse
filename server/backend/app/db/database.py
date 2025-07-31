"""
Smart Greenhouse IoT System - Database Connection
PostgreSQL and TimescaleDB connection management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.models.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()

# Synchronous database engine
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Asynchronous database engine
async_engine = create_async_engine(
    settings.async_database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session makers
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database connection and verify TimescaleDB"""
    try:
        # Test basic PostgreSQL connection first
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            pg_version = result.scalar()
            logger.info(f"PostgreSQL connected: {pg_version}")

        # Check TimescaleDB in a separate transaction to avoid aborting main connection
        if settings.TIMESCALEDB_ENABLED:
            try:
                async with async_engine.begin() as conn:
                    result = await conn.execute(
                        text(
                            "SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
                    )
                    if result.scalar():
                        logger.info("TimescaleDB extension found")
                        # Try version check in another transaction
                        try:
                            async with async_engine.begin() as conn2:
                                result = await conn2.execute(text("SELECT timescaledb_version()"))
                                ts_version = result.scalar()
                                logger.info(
                                    f"TimescaleDB version: {ts_version}")
                        except Exception as e:
                            logger.warning(
                                f"TimescaleDB version check failed: {e}")
                            logger.info(
                                "TimescaleDB extension is installed but version function unavailable")
                    else:
                        logger.warning("TimescaleDB extension not found")
            except Exception as e:
                logger.warning(f"Error checking TimescaleDB: {e}")
                logger.info("Continuing without TimescaleDB verification")

        # Check schemas in a separate transaction
        async with async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('greenhouse', 'monitoring', 'timeseries')")
            )
            schemas = [row[0] for row in result.fetchall()]
            logger.info(f"Available schemas: {schemas}")

            # Test hypertables if TimescaleDB is enabled and timeseries schema exists
            if settings.TIMESCALEDB_ENABLED and 'timeseries' in schemas:
                try:
                    result = await conn.execute(
                        text(
                            "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_schema = 'timeseries'")
                    )
                    hypertables = [row[0] for row in result.fetchall()]
                    logger.info(f"TimescaleDB hypertables: {hypertables}")
                except Exception as e:
                    logger.warning(f"Could not query hypertables: {e}")
                    logger.info(
                        "TimescaleDB information views may not be available")

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get asynchronous database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency to get synchronous database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get asynchronous database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Context manager for database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """Database operations manager"""

    def __init__(self):
        self.engine = async_engine
        self.session_maker = AsyncSessionLocal

    async def health_check(self) -> dict:
        """Check database health status"""
        try:
            async with self.session_maker() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                result.scalar()

                # Check TimescaleDB if enabled
                timescaledb_status = "disabled"
                if settings.TIMESCALEDB_ENABLED:
                    try:
                        result = await session.execute(text("SELECT timescaledb_version()"))
                        version = result.scalar()
                        timescaledb_status = f"enabled - {version}"
                    except Exception:
                        # TimescaleDB extension exists but version function fails
                        try:
                            result = await session.execute(
                                text(
                                    "SELECT extname FROM pg_extension WHERE extname = 'timescaledb'")
                            )
                            if result.scalar():
                                timescaledb_status = "enabled - version check failed"
                            else:
                                timescaledb_status = "extension not found"
                        except Exception:
                            timescaledb_status = "check failed"
                    except:
                        timescaledb_status = "extension not found"

                # Get database size
                result = await session.execute(
                    text(
                        f"SELECT pg_size_pretty(pg_database_size('{settings.POSTGRES_DB}'))")
                )
                db_size = result.scalar()

                # Get connection count
                result = await session.execute(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE datname = :db_name"),
                    {"db_name": settings.POSTGRES_DB}
                )
                connection_count = result.scalar()

                return {
                    "status": "healthy",
                    "database": settings.POSTGRES_DB,
                    "timescaledb": timescaledb_status,
                    "size": db_size,
                    "connections": connection_count
                }

        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_compression_stats(self) -> list:
        """Get TimescaleDB compression statistics"""
        if not settings.TIMESCALEDB_ENABLED:
            return []

        try:
            async with self.session_maker() as session:
                result = await session.execute(text("""
                    SELECT 
                        h.hypertable_name,
                        ROUND((cs.total_bytes / 1024.0 / 1024.0)::numeric, 2) as total_size_mb,
                        ROUND((cs.compressed_total_bytes / 1024.0 / 1024.0)::numeric, 2) as compressed_size_mb,
                        ROUND((100.0 * cs.compressed_total_bytes / NULLIF(cs.total_bytes, 0))::numeric, 1) as compression_ratio,
                        cs.total_chunks,
                        cs.number_compressed_chunks as compressed_chunks
                    FROM timescaledb_information.hypertables h
                    JOIN timescaledb_information.compression_settings cs ON h.hypertable_name = cs.hypertable_name
                    WHERE h.hypertable_schema = 'timeseries'
                    ORDER BY total_size_mb DESC;
                """))

                return [
                    {
                        "table_name": row[0],
                        "total_size_mb": float(row[1]) if row[1] else 0,
                        "compressed_size_mb": float(row[2]) if row[2] else 0,
                        "compression_ratio": float(row[3]) if row[3] else 0,
                        "total_chunks": row[4],
                        "compressed_chunks": row[5]
                    }
                    for row in result.fetchall()
                ]

        except Exception as e:
            logger.error(f"Failed to get compression stats: {str(e)}")
            return []

    async def get_hypertable_info(self) -> list:
        """Get information about TimescaleDB hypertables"""
        if not settings.TIMESCALEDB_ENABLED:
            return []

        try:
            async with self.session_maker() as session:
                result = await session.execute(text("""
                    SELECT 
                        hypertable_schema,
                        hypertable_name,
                        num_dimensions,
                        compression_enabled
                    FROM timescaledb_information.hypertables 
                    WHERE hypertable_schema = 'timeseries'
                    ORDER BY hypertable_name;
                """))

                return [
                    {
                        "schema": row[0],
                        "name": row[1],
                        "dimensions": row[2],
                        "compression_enabled": row[3]
                    }
                    for row in result.fetchall()
                ]

        except Exception as e:
            logger.error(f"Failed to get hypertable info: {str(e)}")
            return []

    async def execute_query(self, query: str, params: dict = None) -> list:
        """Execute a raw SQL query"""
        try:
            async with self.session_maker() as session:
                result = await session.execute(text(query), params or {})
                if result.returns_rows:
                    return [dict(row._mapping) for row in result.fetchall()]
                else:
                    await session.commit()
                    return []

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


async def close_db():
    """Close database connections"""
    try:
        logger.info("Closing database connections...")

        # Close async engine
        if async_engine:
            await async_engine.dispose()
            logger.info("Async database engine closed")

        # Close sync engine
        if engine:
            engine.dispose()
            logger.info("Sync database engine closed")

        logger.info("✅ Database connections closed successfully")

    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def test_db_connection():
    """Test database connection"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        logger.info("Database connection test passed")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
