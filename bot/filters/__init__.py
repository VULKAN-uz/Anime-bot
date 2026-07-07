"""
filters/__init__.py - Maxsus filtrlar
=======================================
Admin va obuna filtrlar.
"""

from aiogram import types
from aiogram.filters import BaseFilter

from bot.config import ADMIN_IDS, CHANNEL_ID, CHANNEL_USERNAME


class IsAdmin(BaseFilter):
    """Admin filtr"""

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMIN_IDS


class IsAdminCallback(BaseFilter):
    """Admin callback filtr"""

    async def __call__(self, callback: types.CallbackQuery) -> bool:
        return callback.from_user.id in ADMIN_IDS


class IsSubscribed(BaseFilter):
    """
    Foydalanuvchi kanalga obuna bo'lganligini tekshirish filtr.
    Agar CHANNEL_ID ko'rsatilmagan bo'lsa, har doim True qaytaradi.
    """

    async def __call__(self, message: types.Message) -> bool:
        if not CHANNEL_ID or CHANNEL_ID == "-1001234567890":
            return True

        try:
            member = await message.bot.get_chat_member(CHANNEL_ID, message.from_user.id)
            return member.status not in ["left", "kicked", "banned"]
        except Exception:
            return True


class IsPrivateChat(BaseFilter):
    """Shaxsiy chat filtri"""

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type == "private"


class IsGroupChat(BaseFilter):
    """Guruh chat filtri"""

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in ["group", "supergroup"]


__all__ = [
    "IsAdmin",
    "IsAdminCallback",
    "IsSubscribed",
    "IsPrivateChat",
    "IsGroupChat",
]
