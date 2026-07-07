"""
middlewares/__init__.py - Middleware lar
=========================================
Logging, rate limiting va user registration middlewares.
"""

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update
from loguru import logger

from bot.config import ADMIN_IDS, RATE_LIMIT
from bot.database.crud import get_or_create_user, update_user_activity
from bot.database.db import AsyncSessionFactory


class DatabaseMiddleware(BaseMiddleware):
    """
    Har bir xabarda ma'lumotlar bazasini session ochadi
    va foydalanuvchini ro'yxatdan o'tkazadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionFactory() as session:
            data["session"] = session

            # Foydalanuvchini aniqlash
            user = None
            if isinstance(event, Message) and event.from_user:
                user = event.from_user
            elif hasattr(event, "from_user") and event.from_user:
                user = event.from_user

            if user and not user.is_bot:
                db_user, created = await get_or_create_user(
                    session,
                    user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
                data["db_user"] = db_user
                if not created:
                    await update_user_activity(session, user.id)

                await session.commit()
            else:
                data["db_user"] = None

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise


class LoggingMiddleware(BaseMiddleware):
    """Barcha xabarlarni log qilish"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_info = ""
        if hasattr(event, "from_user") and event.from_user:
            u = event.from_user
            user_info = f"[{u.id}] @{u.username or u.full_name}"

        event_type = type(event).__name__
        logger.debug(f"📨 {event_type} | {user_info}")

        start_time = time.time()
        result = await handler(event, data)
        elapsed = (time.time() - start_time) * 1000

        logger.debug(f"⏱ {event_type} | {user_info} | {elapsed:.1f}ms")
        return result


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting — bir foydalanuvchi RATE_LIMIT sekundda
    bir marta xabar yuborishi mumkin (adminlar istisno).
    """

    def __init__(self, rate_limit: float = RATE_LIMIT):
        self.rate_limit = rate_limit
        self.last_message: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user or user.id in ADMIN_IDS:
            return await handler(event, data)

        current_time = time.time()
        last_time = self.last_message.get(user.id, 0)
        elapsed = current_time - last_time

        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            logger.warning(f"⚠️ Rate limit: {user.id} | wait={wait_time:.2f}s")
            try:
                await event.answer(
                    f"⏳ Biroz kuting. {wait_time:.1f} soniya keyin yozing.",
                    show_alert=False,
                )
            except Exception:
                pass
            return None

        self.last_message[user.id] = current_time
        return await handler(event, data)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Global xato ushlagichi"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            user_info = ""
            if hasattr(event, "from_user") and event.from_user:
                user_info = f"[{event.from_user.id}]"

            logger.error(f"❌ Xato {user_info}: {type(e).__name__}: {e}", exc_info=True)

            # Foydalanuvchiga xato haqida xabar berish
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "❌ Texnik xato yuz berdi. Iltimos, keyinroq urinib ko'ring."
                    )
            except Exception:
                pass

            raise


__all__ = [
    "DatabaseMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "ErrorHandlerMiddleware",
]
