"""
main.py - Bot asosiy kirish nuqtasi
=====================================
Bot ishga tushirish, middleware va handlerlar ro'yxatga olish.
"""
import asyncio
import sys
from pathlib import Path

from loguru import logger

# Loyiha ildizi
sys.path.insert(0, str(Path(__file__).parent))

from bot.loader import bot, dp
from bot.database.db import init_db, close_db
from bot.middlewares import (
    DatabaseMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from bot.handlers.user import router as user_router
from bot.handlers.admin import router as admin_router
from bot.handlers.search import router as search_router
from bot.handlers.callback import router as callback_router
from bot.config import LOG_FILE, LOG_LEVEL


def setup_logging() -> None:
    """Loguru sozlash"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        LOG_FILE,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )
    logger.info("✅ Logging sozlandi")


def setup_middlewares() -> None:
    """Middleware larni ro'yxatga olish"""
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    logger.info("✅ Middleware lar ro'yxatga olindi")


def setup_routers() -> None:
    """Router larni ro'yxatga olish (tartib muhim!)"""
    # Admin router birinchi (faqat adminlar uchun)
    dp.include_router(admin_router)
    # User router
    dp.include_router(user_router)
    # Callback router
    dp.include_router(callback_router)
    # Search router oxirida (catchall)
    dp.include_router(search_router)
    logger.info("✅ Router lar ro'yxatga olindi")


async def on_startup() -> None:
    """Bot ishga tushganda"""
    logger.info("🚀 Anime Bot ishga tushmoqda...")
    await init_db()
    logger.info("📡 Telegram API ga ulanilmoqda...")
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot tayyor: @{bot_info.username} (ID: {bot_info.id})")


async def on_shutdown() -> None:
    """Bot to'xtaganda"""
    logger.info("🛑 Bot to'xtatilmoqda...")
    await close_db()
    await bot.session.close()
    logger.info("👋 Bot muvaffaqiyatli to'xtatildi.")


async def main() -> None:
    """Asosiy funksiya"""
    setup_logging()
    setup_middlewares()
    setup_routers()

    # Startup va shutdown hooklar
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("📬 Polling boshlanmoqda...")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Bot foydalanuvchi tomonidan to'xtatildi.")
    except Exception as e:
        logger.critical(f"💥 Kutilmagan xato: {e}", exc_info=True)
        sys.exit(1)
