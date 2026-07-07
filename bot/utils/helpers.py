"""
utils/helpers.py - Yordamchi funksiyalar
=========================================
Bot uchun kerakli yordamchi (helper) funksiyalar.
"""

from typing import Optional

from bot.config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    """
    Foydalanuvchi admin ekanligini tekshiradi.
    
    Args:
        user_id: Telegram foydalanuvchi ID si
        
    Returns:
        True - admin, False - oddiy foydalanuvchi.
    """
    return user_id in ADMIN_IDS


def format_anime_info(anime: dict) -> str:
    """
    Anime ma'lumotlarini chiroyli formatda tayyorlaydi.
    
    Args:
        anime: Ma'lumotlar bazasidan olingan anime dict
        
    Returns:
        HTML formatidagi matn.
    """
    return (
        f"🎌 <b>{anime['name']}</b>\n\n"
        f"🔢 <b>Kod:</b> {anime['code']}\n"
        f"🎭 <b>Janr:</b> {anime['genre']}\n"
        f"🌐 <b>Til:</b> {anime['language']}\n"
        f"📺 <b>Qismlar soni:</b> {anime['episodes']}\n\n"
        f"📄 <b>Tavsif:</b>\n{anime['description']}"
    )


def format_anime_list(animes: list[dict]) -> str:
    """
    Animeler ro'yxatini formatlab chiqaradi.
    
    Args:
        animes: Barcha animeler ro'yxati
        
    Returns:
        HTML formatidagi ro'yxat.
    """
    if not animes:
        return "📭 Hozircha hech qanday anime yo'q."

    lines = ["📋 <b>Mavjud animeler:</b>\n"]
    for anime in animes:
        lines.append(f"• <code>{anime['code']}</code> — <b>{anime['name']}</b> ({anime['episodes']} qism)")
    return "\n".join(lines)


def validate_positive_int(value: str) -> Optional[int]:
    """
    Musbat butun sonni tekshiradi.
    
    Returns:
        Son yoki None (noto'g'ri bo'lsa).
    """
    try:
        num = int(value.strip())
        return num if num > 0 else None
    except ValueError:
        return None
