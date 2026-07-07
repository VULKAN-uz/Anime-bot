"""
handlers/user_handler.py - Foydalanuvchi handlerlari
=====================================================
Oddiy foydalanuvchilar uchun:
- /start, /help komandalar
- Anime kodi bo'yicha qidirish
- Tomosha qilish / Yuklab olish callback'lari
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from bot.database import db
from bot.keyboards.user_keyboards import (
    anime_main_keyboard,
    episodes_keyboard,
    back_to_anime_keyboard
)
from bot.utils.helpers import format_anime_info
from bot.config import START_MESSAGE, HELP_MESSAGE

logger = logging.getLogger(__name__)

# Router yaratish
router = Router()


# ==========================================
# /start komandasi
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Bot ishga tushganda xush kelibsiz xabarini yuboradi."""
    await message.answer(
        START_MESSAGE,
        parse_mode="HTML"
    )
    logger.info(f"👤 Yangi foydalanuvchi: {message.from_user.id}")


# ==========================================
# /help komandasi
# ==========================================
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Yordam xabarini yuboradi."""
    await message.answer(HELP_MESSAGE, parse_mode="HTML")


# ==========================================
# Anime kodi bo'yicha qidirish
# ==========================================
@router.message(F.text.regexp(r"^\d+$"))
async def search_anime_by_code(message: Message) -> None:
    """
    Foydalanuvchi raqam yozsa, shu kodli animeni topadi.
    - Poster yuboradi
    - Anime haqida ma'lumot yuboradi
    - Inline tugmalar qo'shadi
    """
    code = int(message.text.strip())
    anime = await db.get_anime_by_code(code)

    # Anime topilmasa
    if not anime:
        await message.answer(
            f"❌ <b>{code}</b> kodli anime topilmadi.\n\n"
            "📋 Mavjud animelар kodini ko'rish uchun ro'yxatga qarang.",
            parse_mode="HTML"
        )
        return

    # Poster va ma'lumot yuborish
    caption = format_anime_info(anime)
    keyboard = anime_main_keyboard(anime["id"])

    if anime.get("poster"):
        await message.answer_photo(
            photo=anime["poster"],
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    logger.info(f"🔍 Foydalanuvchi {message.from_user.id} kod={code} qidirdi")


# ==========================================
# 🎬 Tomosha qilish callback
# ==========================================
@router.callback_query(F.data.startswith("watch:"))
async def watch_callback(callback: CallbackQuery) -> None:
    """
    "Tomosha qilish" bosilganda qismlar ro'yxatini chiqaradi.
    Callback data: watch:{anime_id}
    """
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)

    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    total = anime["episodes"]
    if total == 0:
        await callback.answer("⚠️ Bu animeda hali qism yo'q!", show_alert=True)
        return

    keyboard = episodes_keyboard(anime_id, total, action="watch")
    await callback.message.edit_caption(
        caption=f"🎬 <b>{anime['name']}</b> — Qismni tanlang:\n\n"
                f"📺 Jami: <b>{total}</b> qism",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ==========================================
# 📥 Yuklab olish callback
# ==========================================
@router.callback_query(F.data.startswith("download:"))
async def download_callback(callback: CallbackQuery) -> None:
    """
    "Yuklab olish" bosilganda qismlar ro'yxatini chiqaradi.
    Callback data: download:{anime_id}
    """
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)

    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    total = anime["episodes"]
    if total == 0:
        await callback.answer("⚠️ Bu animeda hali qism yo'q!", show_alert=True)
        return

    keyboard = episodes_keyboard(anime_id, total, action="download")
    await callback.message.edit_caption(
        caption=f"📥 <b>{anime['name']}</b> — Yuklab olinadigan qismni tanlang:\n\n"
                f"📺 Jami: <b>{total}</b> qism",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ==========================================
# Qism tanlash callback (tomosha / yuklab olish)
# ==========================================
@router.callback_query(F.data.startswith("ep:"))
async def episode_callback(callback: CallbackQuery) -> None:
    """
    Qism tanlanganda video yuboradi.
    Callback data: ep:{action}:{anime_id}:{episode_num}
    
    action = "watch"    → video yuboradi (tomosha)
    action = "download" → video yuboradi (download sifatida)
    """
    parts = callback.data.split(":")
    action      = parts[1]           # watch | download
    anime_id    = int(parts[2])
    episode_num = int(parts[3])

    # Anime ma'lumotlarini olish
    anime = await db.get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    # file_id ni olish
    file_id = await db.get_episode(anime_id, episode_num)
    if not file_id:
        await callback.answer(
            f"⚠️ {episode_num}-qism hali yuklanmagan!",
            show_alert=True
        )
        return

    await callback.answer(f"⏳ {episode_num}-qism yuborilmoqda...")

    # Sarlavha
    caption = (
        f"🎌 <b>{anime['name']}</b>\n"
        f"📺 <b>{episode_num}-qism</b>"
    )

    if action == "watch":
        # Tomosha qilish — video sifatida yuborish
        await callback.message.answer_video(
            video=file_id,
            caption=caption,
            parse_mode="HTML"
        )
    else:
        # Yuklab olish — document sifatida yuborish
        await callback.message.answer_document(
            document=file_id,
            caption=caption,
            parse_mode="HTML"
        )

    logger.info(
        f"📤 Foydalanuvchi {callback.from_user.id}: "
        f"anime_id={anime_id}, ep={episode_num}, action={action}"
    )


# ==========================================
# Orqaga qaytish callback
# ==========================================
@router.callback_query(F.data.startswith("back_to_anime:"))
async def back_to_anime_callback(callback: CallbackQuery) -> None:
    """
    Orqaga bosilganda anime kartochkasiga qaytadi.
    Callback data: back_to_anime:{anime_id}
    """
    anime_id = int(callback.data.split(":")[1])
    anime = await db.get_anime_by_id(anime_id)

    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    keyboard = anime_main_keyboard(anime_id)
    caption = format_anime_info(anime)

    await callback.message.edit_caption(
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
