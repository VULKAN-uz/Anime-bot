"""
database/crud.py - CRUD operatsiyalari
========================================
Barcha ma'lumotlar bazasi operatsiyalari shu yerda.
"""

from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import (
    Anime,
    BotSettings,
    BroadcastMessage,
    Episode,
    Favorite,
    SearchHistory,
    User,
)


# ==========================================
# USER CRUD
# ==========================================

async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    """Foydalanuvchini user_id bo'yicha olish"""
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str],
    full_name: str,
) -> User:
    """Yangi foydalanuvchi yaratish"""
    user = User(
        user_id=user_id,
        username=username,
        full_name=full_name,
        is_subscribed=False,
    )
    session.add(user)
    await session.flush()
    logger.info(f"👤 Yangi foydalanuvchi: {user_id} - {full_name}")
    return user


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: Optional[str],
    full_name: str,
) -> tuple[User, bool]:
    """Foydalanuvchini olish yoki yaratish. (user, created) qaytaradi"""
    user = await get_user(session, user_id)
    if user is None:
        user = await create_user(session, user_id, username, full_name)
        return user, True
    else:
        # Ma'lumotlarni yangilash
        user.username = username
        user.full_name = full_name
        user.is_active = True
        user.last_activity = datetime.utcnow()
        return user, False


async def update_user_activity(session: AsyncSession, user_id: int) -> None:
    """Foydalanuvchi faolligini yangilash"""
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(last_activity=datetime.utcnow(), is_active=True)
    )


async def update_user_subscription(
    session: AsyncSession, user_id: int, is_subscribed: bool
) -> None:
    """Foydalanuvchi obuna holatini yangilash"""
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(is_subscribed=is_subscribed)
    )


async def block_user(session: AsyncSession, user_id: int) -> None:
    """Foydalanuvchini bloklash"""
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(is_blocked=True, is_active=False)
    )


async def get_all_active_users(session: AsyncSession) -> list[User]:
    """Barcha faol foydalanuvchilarni olish"""
    result = await session.execute(
        select(User).where(User.is_active == True, User.is_blocked == False)
    )
    return list(result.scalars().all())


async def get_users_count(session: AsyncSession) -> int:
    """Foydalanuvchilar sonini olish"""
    result = await session.execute(select(func.count(User.id)))
    return result.scalar_one()


async def get_today_users_count(session: AsyncSession) -> int:
    """Bugungi yangi foydalanuvchilar sonini olish"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )
    return result.scalar_one()


async def get_active_users_count(session: AsyncSession) -> int:
    """Faol foydalanuvchilar sonini olish (so'nggi 24 soat)"""
    since = datetime.utcnow() - timedelta(hours=24)
    result = await session.execute(
        select(func.count(User.id)).where(User.last_activity >= since)
    )
    return result.scalar_one()


async def increment_user_searches(session: AsyncSession, user_id: int) -> None:
    """Foydalanuvchi qidiruvlari sonini oshirish"""
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(searches_count=User.searches_count + 1)
    )


async def get_all_user_ids(session: AsyncSession) -> list[int]:
    """Barcha foydalanuvchi ID larini olish (broadcast uchun)"""
    result = await session.execute(
        select(User.user_id).where(
            User.is_active == True,
            User.is_blocked == False
        )
    )
    return list(result.scalars().all())


# ==========================================
# ANIME CRUD
# ==========================================

async def get_anime_by_code(session: AsyncSession, code: int) -> Optional[Anime]:
    """Anime kodini topish"""
    result = await session.execute(
        select(Anime)
        .where(Anime.code == code, Anime.is_active == True)
        .options(selectinload(Anime.episodes))
    )
    return result.scalar_one_or_none()


async def get_anime_by_id(session: AsyncSession, anime_id: int) -> Optional[Anime]:
    """Anime ID bo'yicha topish"""
    result = await session.execute(
        select(Anime)
        .where(Anime.id == anime_id, Anime.is_active == True)
        .options(selectinload(Anime.episodes))
    )
    return result.scalar_one_or_none()


async def get_animes_paginated(
    session: AsyncSession, page: int = 1, per_page: int = 20
) -> tuple[list[Anime], int]:
    """Animelarni pagination bilan olish"""
    offset = (page - 1) * per_page

    # Jami son
    count_result = await session.execute(
        select(func.count(Anime.id)).where(Anime.is_active == True)
    )
    total = count_result.scalar_one()

    # Animelar
    result = await session.execute(
        select(Anime)
        .where(Anime.is_active == True)
        .order_by(Anime.code)
        .offset(offset)
        .limit(per_page)
    )
    animes = list(result.scalars().all())

    return animes, total


async def search_anime_by_name(
    session: AsyncSession, query: str
) -> list[Anime]:
    """Anime nomini qidirish"""
    result = await session.execute(
        select(Anime)
        .where(
            Anime.is_active == True,
            Anime.name.ilike(f"%{query}%")
        )
        .order_by(Anime.searches_count.desc())
        .limit(10)
    )
    return list(result.scalars().all())


async def get_all_animes(session: AsyncSession) -> list[Anime]:
    """Barcha animelarni olish"""
    result = await session.execute(
        select(Anime)
        .where(Anime.is_active == True)
        .options(selectinload(Anime.episodes))
        .order_by(Anime.code)
    )
    return list(result.scalars().all())


async def get_animes_count(session: AsyncSession) -> int:
    """Animeler sonini olish"""
    result = await session.execute(
        select(func.count(Anime.id)).where(Anime.is_active == True)
    )
    return result.scalar_one()


async def get_next_anime_code(session: AsyncSession) -> int:
    """Keyingi anime kodi (avtomatik)"""
    result = await session.execute(
        select(func.max(Anime.code))
    )
    max_code = result.scalar_one()
    return (max_code or 0) + 1


async def create_anime(
    session: AsyncSession,
    code: int,
    name: str,
    description: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    duration: Optional[str] = None,
    language: Optional[str] = None,
    rating: Optional[float] = None,
    episodes_count: int = 0,
    poster_file_id: Optional[str] = None,
    status: str = "ongoing",
    name_en: Optional[str] = None,
) -> Anime:
    """Yangi anime yaratish"""
    anime = Anime(
        code=code,
        name=name,
        name_en=name_en,
        description=description,
        genre=genre,
        year=year,
        duration=duration,
        language=language,
        rating=rating,
        episodes_count=episodes_count,
        poster_file_id=poster_file_id,
        status=status,
    )
    session.add(anime)
    await session.flush()
    logger.info(f"🎬 Yangi anime qo'shildi: {code} - {name}")
    return anime


async def update_anime(
    session: AsyncSession,
    anime_id: int,
    **kwargs,
) -> Optional[Anime]:
    """Animeni yangilash"""
    await session.execute(
        update(Anime).where(Anime.id == anime_id).values(**kwargs)
    )
    return await get_anime_by_id(session, anime_id)


async def delete_anime(session: AsyncSession, anime_id: int) -> bool:
    """Animeni o'chirish (soft delete)"""
    result = await session.execute(
        update(Anime)
        .where(Anime.id == anime_id)
        .values(is_active=False)
    )
    return result.rowcount > 0


async def increment_anime_searches(session: AsyncSession, anime_id: int) -> None:
    """Anime qidiruvlari sonini oshirish"""
    await session.execute(
        update(Anime)
        .where(Anime.id == anime_id)
        .values(searches_count=Anime.searches_count + 1)
    )


async def increment_anime_views(session: AsyncSession, anime_id: int) -> None:
    """Anime ko'rishlar sonini oshirish"""
    await session.execute(
        update(Anime)
        .where(Anime.id == anime_id)
        .values(views_count=Anime.views_count + 1)
    )


async def update_anime_poster(
    session: AsyncSession, anime_id: int, poster_file_id: str
) -> None:
    """Anime posterini yangilash"""
    await session.execute(
        update(Anime)
        .where(Anime.id == anime_id)
        .values(poster_file_id=poster_file_id)
    )


# ==========================================
# EPISODE CRUD
# ==========================================

async def get_episodes_by_anime(
    session: AsyncSession, anime_id: int
) -> list[Episode]:
    """Anime qismlarini olish"""
    result = await session.execute(
        select(Episode)
        .where(Episode.anime_id == anime_id)
        .order_by(Episode.episode_number)
    )
    return list(result.scalars().all())


async def get_episode(
    session: AsyncSession, anime_id: int, episode_number: int
) -> Optional[Episode]:
    """Muayyan qismni olish"""
    result = await session.execute(
        select(Episode).where(
            Episode.anime_id == anime_id,
            Episode.episode_number == episode_number,
        )
    )
    return result.scalar_one_or_none()


async def create_episode(
    session: AsyncSession,
    anime_id: int,
    episode_number: int,
    file_id: str,
    file_unique_id: Optional[str] = None,
    title: Optional[str] = None,
    duration: Optional[int] = None,
    file_size: Optional[int] = None,
) -> Episode:
    """Yangi qism yaratish"""
    episode = Episode(
        anime_id=anime_id,
        episode_number=episode_number,
        file_id=file_id,
        file_unique_id=file_unique_id,
        title=title,
        duration=duration,
        file_size=file_size,
    )
    session.add(episode)
    await session.flush()

    # Anime qismlar sonini yangilash
    count_result = await session.execute(
        select(func.count(Episode.id)).where(Episode.anime_id == anime_id)
    )
    count = count_result.scalar_one()
    await session.execute(
        update(Anime)
        .where(Anime.id == anime_id)
        .values(episodes_count=count)
    )

    logger.info(f"🎞 Yangi qism qo'shildi: anime_id={anime_id}, ep={episode_number}")
    return episode


async def delete_episode(
    session: AsyncSession, anime_id: int, episode_number: int
) -> bool:
    """Qismni o'chirish"""
    result = await session.execute(
        delete(Episode).where(
            Episode.anime_id == anime_id,
            Episode.episode_number == episode_number,
        )
    )
    if result.rowcount > 0:
        # Anime qismlar sonini yangilash
        count_result = await session.execute(
            select(func.count(Episode.id)).where(Episode.anime_id == anime_id)
        )
        count = count_result.scalar_one()
        await session.execute(
            update(Anime)
            .where(Anime.id == anime_id)
            .values(episodes_count=count)
        )
        return True
    return False


async def get_videos_count(session: AsyncSession) -> int:
    """Jami video (qism) sonini olish"""
    result = await session.execute(select(func.count(Episode.id)))
    return result.scalar_one()


async def increment_episode_views(
    session: AsyncSession, episode_id: int
) -> None:
    """Qism ko'rishlar sonini oshirish"""
    await session.execute(
        update(Episode)
        .where(Episode.id == episode_id)
        .values(views_count=Episode.views_count + 1)
    )


async def increment_episode_downloads(
    session: AsyncSession, episode_id: int
) -> None:
    """Qism yuklab olishlar sonini oshirish"""
    await session.execute(
        update(Episode)
        .where(Episode.id == episode_id)
        .values(downloads_count=Episode.downloads_count + 1)
    )


# ==========================================
# FAVORITES CRUD
# ==========================================

async def add_favorite(
    session: AsyncSession, user_db_id: int, anime_id: int
) -> tuple[Favorite, bool]:
    """Sevimliga qo'shish. (favorite, created) qaytaradi"""
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_db_id,
            Favorite.anime_id == anime_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False

    favorite = Favorite(user_id=user_db_id, anime_id=anime_id)
    session.add(favorite)
    await session.flush()
    return favorite, True


async def remove_favorite(
    session: AsyncSession, user_db_id: int, anime_id: int
) -> bool:
    """Sevimlilardan o'chirish"""
    result = await session.execute(
        delete(Favorite).where(
            Favorite.user_id == user_db_id,
            Favorite.anime_id == anime_id,
        )
    )
    return result.rowcount > 0


async def get_user_favorites(
    session: AsyncSession, user_db_id: int
) -> list[Anime]:
    """Foydalanuvchi sevimlilarini olish"""
    result = await session.execute(
        select(Anime)
        .join(Favorite, Favorite.anime_id == Anime.id)
        .where(Favorite.user_id == user_db_id, Anime.is_active == True)
        .order_by(Favorite.created_at.desc())
    )
    return list(result.scalars().all())


async def is_favorite(
    session: AsyncSession, user_db_id: int, anime_id: int
) -> bool:
    """Anime sevimlilar ro'yxatidami?"""
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_db_id,
            Favorite.anime_id == anime_id,
        )
    )
    return result.scalar_one_or_none() is not None


# ==========================================
# SEARCH HISTORY
# ==========================================

async def add_search_history(
    session: AsyncSession,
    user_db_id: int,
    query: str,
    anime_code: Optional[int] = None,
    found: bool = True,
) -> None:
    """Qidiruv tarixiga qo'shish"""
    history = SearchHistory(
        user_id=user_db_id,
        query=query,
        anime_code=anime_code,
        found=found,
    )
    session.add(history)


async def get_total_searches(session: AsyncSession) -> int:
    """Jami qidiruvlar soni"""
    result = await session.execute(select(func.count(SearchHistory.id)))
    return result.scalar_one()


# ==========================================
# BROADCAST
# ==========================================

async def create_broadcast(
    session: AsyncSession,
    admin_id: int,
    message_text: Optional[str],
    media_file_id: Optional[str] = None,
    media_type: Optional[str] = None,
) -> BroadcastMessage:
    """Broadcast yaratish"""
    broadcast = BroadcastMessage(
        admin_id=admin_id,
        message_text=message_text,
        media_file_id=media_file_id,
        media_type=media_type,
        status="pending",
    )
    session.add(broadcast)
    await session.flush()
    return broadcast


async def update_broadcast_status(
    session: AsyncSession,
    broadcast_id: int,
    sent_count: int,
    failed_count: int,
    status: str,
) -> None:
    """Broadcast holatini yangilash"""
    await session.execute(
        update(BroadcastMessage)
        .where(BroadcastMessage.id == broadcast_id)
        .values(
            sent_count=sent_count,
            failed_count=failed_count,
            status=status,
            completed_at=datetime.utcnow(),
        )
    )


# ==========================================
# BOT SETTINGS
# ==========================================

async def get_setting(
    session: AsyncSession, key: str, default: str = ""
) -> str:
    """Sozlamani olish"""
    result = await session.execute(
        select(BotSettings).where(BotSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(
    session: AsyncSession,
    key: str,
    value: str,
    description: Optional[str] = None,
) -> None:
    """Sozlamani o'rnatish"""
    result = await session.execute(
        select(BotSettings).where(BotSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = BotSettings(key=key, value=value, description=description)
        session.add(setting)


# ==========================================
# STATISTIKA
# ==========================================

async def get_full_stats(session: AsyncSession) -> dict:
    """To'liq statistika"""
    users_count = await get_users_count(session)
    today_users = await get_today_users_count(session)
    active_users = await get_active_users_count(session)
    animes_count = await get_animes_count(session)
    videos_count = await get_videos_count(session)
    searches_count = await get_total_searches(session)

    return {
        "users_count": users_count,
        "today_users": today_users,
        "active_users": active_users,
        "animes_count": animes_count,
        "videos_count": videos_count,
        "searches_count": searches_count,
    }
