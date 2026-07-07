"""
utils/__init__.py - Yordamchi funksiyalar
==========================================
Anime ma'lumotlarini formatlash, rasm qidiruv API va boshqalar.
"""

import asyncio
import hashlib
import io
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp
from loguru import logger

from bot.config import BACKUP_DIR, DATABASE_PATH, IMAGES_DIR
from bot.database.models import Anime, Episode


def format_anime_info(anime: Anime) -> str:
    """Anime ma'lumotlarini chiroyli formatda chiqarish"""
    rating_stars = ""
    if anime.rating:
        full_stars = int(anime.rating / 2)
        rating_stars = "⭐" * full_stars

    status_emoji = {
        "ongoing": "📺 Davom etmoqda",
        "completed": "✅ Tugagan",
        "paused": "⏸ To'xtatilgan",
    }.get(anime.status, "❓ Noma'lum")

    text = f"""
🎌 <b>{anime.name}</b>

🆔 <b>Kod:</b> <code>{anime.code}</code>
🎭 <b>Janr:</b> {anime.genre or 'Noma\'lum'}
📅 <b>Yili:</b> {anime.year or 'Noma\'lum'}
⏱ <b>Davomiyligi:</b> {anime.duration or 'Noma\'lum'}
🌐 <b>Tili:</b> {anime.language or 'Noma\'lum'}
⭐ <b>Reyting:</b> {f'{anime.rating}/10 {rating_stars}' if anime.rating else 'Noma\'lum'}
🎬 <b>Qismlar:</b> {anime.episodes_count} ta
📊 <b>Holat:</b> {status_emoji}
🔍 <b>Qidiruvlar:</b> {anime.searches_count} marta

📖 <b>Tavsif:</b>
{anime.description or 'Tavsif mavjud emas.'}
""".strip()

    return text


def format_file_size(size_bytes: Optional[int]) -> str:
    """Fayl hajmini formatlash"""
    if not size_bytes:
        return "Noma'lum"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def format_duration(seconds: Optional[int]) -> str:
    """Davomiylikni formatlash"""
    if not seconds:
        return "Noma'lum"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_stats(stats: dict) -> str:
    """Statistikani chiroyli formatda chiqarish"""
    return f"""
📊 <b>Bot Statistikasi</b>
━━━━━━━━━━━━━━━━━━━━━━━━

👥 <b>Foydalanuvchilar:</b>
  • Jami: <b>{stats['users_count']}</b> ta
  • Bugungi yangilar: <b>{stats['today_users']}</b> ta
  • Faol (24 soat): <b>{stats['active_users']}</b> ta

🎬 <b>Kontent:</b>
  • Animeler: <b>{stats['animes_count']}</b> ta
  • Videolar: <b>{stats['videos_count']}</b> ta

🔍 <b>Faollik:</b>
  • Jami qidiruvlar: <b>{stats['searches_count']}</b> ta

🕐 <b>Yangilangan:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


async def check_subscription(bot, user_id: int, channel_id: str) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganligini tekshirish"""
    if not channel_id or channel_id == "-1001234567890":
        return True
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except Exception as e:
        logger.warning(f"Obuna tekshirishda xato: {e}")
        return True


async def search_anime_by_image(image_data: bytes) -> Optional[list[dict]]:
    """
    Rasm orqali anime qidirish (trace.moe API).
    https://soruly.github.io/trace.moe-api/
    """
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field(
                "image",
                image_data,
                filename="image.jpg",
                content_type="image/jpeg",
            )

            async with session.post(
                "https://api.trace.moe/search",
                data=form,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("result", [])
                    return results[:5]  # Eng yaxshi 5 natija
                else:
                    logger.warning(f"trace.moe API xatosi: {response.status}")
                    return None
    except asyncio.TimeoutError:
        logger.warning("trace.moe API timeout")
        return None
    except Exception as e:
        logger.error(f"Rasm qidiruvda xato: {e}")
        return None


def format_image_search_results(results: list[dict]) -> str:
    """Rasm qidiruv natijalarini formatlash"""
    if not results:
        return "❌ Hech qanday natija topilmadi."

    text = "🖼 <b>Rasm bo'yicha topilgan animelar:</b>\n\n"

    for i, result in enumerate(results, 1):
        anilist_info = result.get("anilist", {})
        title = "Noma'lum"

        if isinstance(anilist_info, dict):
            titles = anilist_info.get("title", {})
            title = (
                titles.get("romaji")
                or titles.get("english")
                or titles.get("native")
                or "Noma'lum"
            )

        similarity = result.get("similarity", 0) * 100
        episode = result.get("episode", "?")
        from_time = result.get("from", 0)
        to_time = result.get("to", 0)

        minutes = int(from_time // 60)
        seconds = int(from_time % 60)

        text += (
            f"<b>{i}. {title}</b>\n"
            f"   🎬 Qism: {episode}\n"
            f"   ⏱ Vaqt: {minutes}:{seconds:02d}\n"
            f"   📊 O'xshashlik: {similarity:.1f}%\n\n"
        )

    text += "💡 <i>Botdagi anime kodini yozing yoki 🎬 Anime tugmasini bosing.</i>"
    return text


async def create_backup() -> Optional[str]:
    """Ma'lumotlar bazasini backup qilish"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"anime_bot_{timestamp}.db"

        # SQLite backup
        source = sqlite3.connect(DATABASE_PATH)
        backup = sqlite3.connect(str(backup_file))

        with backup:
            source.backup(backup)

        source.close()
        backup.close()

        size = backup_file.stat().st_size
        logger.info(f"✅ Backup yaratildi: {backup_file} ({format_file_size(size)})")
        return str(backup_file)

    except Exception as e:
        logger.error(f"❌ Backup yaratishda xato: {e}")
        return None


async def restore_backup(backup_path: str) -> bool:
    """Backup'dan tiklash"""
    try:
        if not Path(backup_path).exists():
            logger.error(f"Backup fayl topilmadi: {backup_path}")
            return False

        # Joriy bazani zaxiralash
        current_backup = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DATABASE_PATH, current_backup)

        # Tiklash
        source = sqlite3.connect(backup_path)
        target = sqlite3.connect(DATABASE_PATH)

        with target:
            source.backup(target)

        source.close()
        target.close()

        logger.info(f"✅ Backup tiklandi: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Tiklashda xato: {e}")
        return False


def get_backup_list() -> list[dict]:
    """Mavjud backup'lar ro'yxati"""
    backups = []
    try:
        for f in sorted(BACKUP_DIR.glob("*.db"), reverse=True)[:10]:
            backups.append({
                "name": f.name,
                "path": str(f),
                "size": format_file_size(f.stat().st_size),
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                    "%d.%m.%Y %H:%M"
                ),
            })
    except Exception as e:
        logger.error(f"Backup ro'yxatida xato: {e}")

    return backups


def paginate_list(items: list, page: int, per_page: int) -> tuple[list, int]:
    """Ro'yxatni pagination qilish"""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total


def truncate_text(text: str, max_length: int = 200) -> str:
    """Matnni qisqartirish"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Fayl nomini tozalash"""
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip()


__all__ = [
    "format_anime_info",
    "format_file_size",
    "format_duration",
    "format_stats",
    "check_subscription",
    "search_anime_by_image",
    "format_image_search_results",
    "create_backup",
    "restore_backup",
    "get_backup_list",
    "paginate_list",
    "truncate_text",
    "sanitize_filename",
]
