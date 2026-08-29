import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("weathergpt.database")

RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/weathergpt",
)

if RAW_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
elif RAW_DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = RAW_DATABASE_URL
else:
    raise RuntimeError(
        "DATABASE_URL must be a postgresql:// connection string, "
        f"got: {RAW_DATABASE_URL!r}"
    )

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with SessionLocal() as session:
        yield session


async def init_db(retries: int = 15, delay_seconds: float = 2.0) -> None:
    from models import db_models  # noqa: F401

    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database ready (extensions + tables verified).")
            return
        except Exception as exc:  # noqa: BLE001 - we want to retry on anything
            last_error = exc
            logger.warning(
                "Database not ready yet (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            await asyncio.sleep(delay_seconds)

    raise RuntimeError(
        f"Could not initialize the database after {retries} attempts"
    ) from last_error
