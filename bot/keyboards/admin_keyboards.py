"""
keyboards/admin_keyboards.py - Admin klaviaturalari
====================================================
Admin paneli uchun reply va inline klaviaturalar.
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Admin bosh menyu klaviaturasi.
    
    Tugmalar:
    ➕ Anime qo'shish | 🎬 Qism yuklash
    ✏️ Tahrirlash    | 🗑 O'chirish
    📋 Animlar ro'yxati
    """
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Anime qo'shish"),
        KeyboardButton(text="🎬 Qism yuklash")
    )
    builder.row(
        KeyboardButton(text="✏️ Tahrirlash"),
        KeyboardButton(text="🗑 O'chirish")
    )
    builder.row(
        KeyboardButton(text="📋 Animlar ro'yxati")
    )
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash / Bekor qilish tugmalari."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="✅ Ha, o'chirish"),
        KeyboardButton(text="❌ Bekor qilish")
    )
    return builder.as_markup(resize_keyboard=True)


def edit_fields_keyboard() -> InlineKeyboardMarkup:
    """Anime maydonlarini tanlash uchun inline klaviatura."""
    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Nomi",       "edit_field:name"),
        ("🖼 Posteri",    "edit_field:poster"),
        ("🎭 Janri",      "edit_field:genre"),
        ("🌐 Tili",       "edit_field:language"),
        ("📄 Tavsifi",    "edit_field:description"),
        ("📺 Qismlar soni", "edit_field:episodes"),
        ("🔢 Kodi",       "edit_field:code"),
    ]
    for text, data in fields:
        builder.button(text=text, callback_data=data)
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="edit_cancel")
    )
    return builder.as_markup()
