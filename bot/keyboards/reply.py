"""
keyboards/reply.py - Reply Keyboard tugmalari
==============================================
Asosiy foydalanuvchi va admin reply klaviaturalari.
"""

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

remove_keyboard = ReplyKeyboardRemove()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy foydalanuvchi klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🆔 Kod orqali qidiruv"),
                KeyboardButton(text="🎬 Anime"),
            ],
            [
                KeyboardButton(text="🖼 Rasm orqali qidiruv"),
                KeyboardButton(text="📚 Qo'llanma"),
            ],
            [
                KeyboardButton(text="📋 Ro'yxat"),
                KeyboardButton(text="📢 Reklama"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Anime kodi yoki qo'shimcha buyruqni kiriting...",
    )
    return keyboard


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish va bekor qilish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Ha, tasdiqlash"),
                KeyboardButton(text="❌ Yo'q, bekor"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Admin asosiy klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Anime qo'shish"),
                KeyboardButton(text="✏️ Anime tahrirlash"),
            ],
            [
                KeyboardButton(text="🗑 Anime o'chirish"),
                KeyboardButton(text="🖼 Poster almashtirish"),
            ],
            [
                KeyboardButton(text="🎬 Qism qo'shish"),
                KeyboardButton(text="❌ Qism o'chirish"),
            ],
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="👤 Foydalanuvchilar"),
            ],
            [
                KeyboardButton(text="📢 Reklama yuborish"),
                KeyboardButton(text="⚙️ Sozlamalar"),
            ],
            [
                KeyboardButton(text="💾 Backup yaratish"),
                KeyboardButton(text="🔙 Asosiy menyu"),
            ],
        ],
        resize_keyboard=True,
    )
    return keyboard


def get_more_episodes_keyboard() -> ReplyKeyboardMarkup:
    """Yana qism qo'shish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Yana qism qo'shish"),
                KeyboardButton(text="✅ Tugatish"),
            ],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_status_keyboard() -> ReplyKeyboardMarkup:
    """Anime status tanlash klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📺 ongoing"),
                KeyboardButton(text="✅ completed"),
                KeyboardButton(text="⏸ paused"),
            ],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard
