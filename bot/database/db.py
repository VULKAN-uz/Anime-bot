"""
database/db.py - Ma'lumotlar bazasi ulanishi
=============================================
Async SQLAlchemy session va engine yaratadi.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import DATABASE_URL
from bot.database.models import Base

# Async engine yaratish
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Ma'lumotlar bazasini ishga tushirish va jadvallarni yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")


async def close_db() -> None:
    """Ma'lumotlar bazasi ulanishini yopish"""
    await engine.dispose()
    logger.info("🔌 Ma'lumotlar bazasi ulanishi yopildi")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager sifatida async session olish"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Database session xatosi: {e}")
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection uchun session generator"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
