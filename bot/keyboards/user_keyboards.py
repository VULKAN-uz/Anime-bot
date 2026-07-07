"""
keyboards/user_keyboards.py - Foydalanuvchi klaviaturalari
===========================================================
Foydalanuvchilarga ko'rsatiladigan inline va reply klaviaturalar.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def anime_main_keyboard(anime_id: int) -> InlineKeyboardMarkup:
    """
    Anime kartochkasidagi asosiy tugmalar.
    
    Args:
        anime_id: Anime ID si (callback uchun)
        
    Returns:
        2 ta tugmali inline klaviatura:
        🎬 Tomosha qilish | 📥 Yuklab olish
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🎬 Tomosha qilish",
            callback_data=f"watch:{anime_id}"
        ),
        InlineKeyboardButton(
            text="📥 Yuklab olish",
            callback_data=f"download:{anime_id}"
        )
    )
    return builder.as_markup()


def episodes_keyboard(anime_id: int, total_episodes: int, action: str) -> InlineKeyboardMarkup:
    """
    Qismlar ro'yxati klaviaturasi.
    
    Args:
        anime_id: Anime ID si
        total_episodes: Umumiy qismlar soni
        action: "watch" yoki "download"
        
    Returns:
        Qismlar tugmalari (4 ta ustun), pastida "⬅️ Orqaga" tugmasi.
    """
    builder = InlineKeyboardBuilder()

    # Qismlar tugmalari (4 ustunli)
    buttons = [
        InlineKeyboardButton(
            text=f"{i}-qism",
            callback_data=f"ep:{action}:{anime_id}:{i}"
        )
        for i in range(1, total_episodes + 1)
    ]
    builder.add(*buttons)
    builder.adjust(4)  # 4 ta ustun

    # Orqaga tugmasi
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data=f"back_to_anime:{anime_id}"
        )
    )
    return builder.as_markup()


def back_to_anime_keyboard(anime_id: int) -> InlineKeyboardMarkup:
    """Orqaga qaytish tugmasi."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⬅️ Orqaga",
        callback_data=f"back_to_anime:{anime_id}"
    )
    return builder.as_markup()
