"""
keyboards/inline.py - Inline Keyboard tugmalari
=================================================
Barcha inline klaviaturalar shu yerda.
"""

import math

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ANIME_PER_PAGE, CHANNEL_USERNAME
from bot.database.models import Anime, Episode


def get_anime_detail_keyboard(
    anime: Anime,
    is_favorite: bool = False,
) -> InlineKeyboardMarkup:
    """Anime tafsilotlari uchun inline klaviatura"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🎬 Tomosha qilish",
            callback_data=f"watch:{anime.id}",
        ),
        InlineKeyboardButton(
            text="📥 Yuklab olish",
            callback_data=f"download:{anime.id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="❤️ Sevimlilardan olib tashlash" if is_favorite else "🤍 Sevimlilarga qo'shish",
            callback_data=f"unfav:{anime.id}" if is_favorite else f"fav:{anime.id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="back_to_list",
        ),
    )

    return builder.as_markup()


def get_episodes_keyboard(
    anime: Anime,
    episodes: list[Episode],
    action: str = "watch",
    page: int = 1,
) -> InlineKeyboardMarkup:
    """Qismlar tanlash klaviaturasi (watch yoki download)"""
    builder = InlineKeyboardBuilder()

    per_page = 12
    total_pages = max(1, math.ceil(len(episodes) / per_page))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_episodes = episodes[start_idx:end_idx]

    # Qismlarni 3 tadan qator qilib chiqarish
    row_buttons = []
    for ep in current_episodes:
        row_buttons.append(
            InlineKeyboardButton(
                text=f"▶️ {ep.episode_number}-qism" if action == "watch" else f"📥 {ep.episode_number}-qism",
                callback_data=f"ep_{action}:{anime.id}:{ep.episode_number}",
            )
        )
        if len(row_buttons) == 3:
            builder.row(*row_buttons)
            row_buttons = []

    if row_buttons:
        builder.row(*row_buttons)

    # Pagination
    nav_buttons = []
    if total_pages > 1:
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"ep_page:{action}:{anime.id}:{page - 1}",
                )
            )
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="noop",
            )
        )
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"ep_page:{action}:{anime.id}:{page + 1}",
                )
            )
        if nav_buttons:
            builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"anime:{anime.id}",
        )
    )

    return builder.as_markup()


def get_anime_list_keyboard(
    animes: list[Anime],
    page: int = 1,
    total: int = 0,
    per_page: int = ANIME_PER_PAGE,
) -> InlineKeyboardMarkup:
    """Animelar ro'yxati klaviaturasi (pagination bilan)"""
    builder = InlineKeyboardBuilder()

    total_pages = max(1, math.ceil(total / per_page))

    for anime in animes:
        builder.row(
            InlineKeyboardButton(
                text=f"#{anime.code} | {anime.name} ({anime.year or '?'}) • {anime.episodes_count} qism",
                callback_data=f"anime:{anime.id}",
            )
        )

    # Pagination tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"anime_list:{page - 1}",
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="noop",
        )
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"anime_list:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Obuna klaviaturasi"""
    builder = InlineKeyboardBuilder()

    channel = CHANNEL_USERNAME or "@your_channel"
    builder.row(
        InlineKeyboardButton(
            text="📢 Kanalga obuna bo'lish",
            url=f"https://t.me/{channel.lstrip('@')}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription",
        )
    )

    return builder.as_markup()


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Admin panel inline klaviaturasi"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="➕ Anime qo'shish", callback_data="admin:add_anime"),
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="admin:edit_anime"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 O'chirish", callback_data="admin:delete_anime"),
        InlineKeyboardButton(text="🖼 Poster", callback_data="admin:change_poster"),
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Qism qo'sh", callback_data="admin:add_episode"),
        InlineKeyboardButton(text="❌ Qism o'chir", callback_data="admin:delete_episode"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
        InlineKeyboardButton(text="👤 Foydalanuvchilar", callback_data="admin:users"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin:settings"),
    )
    builder.row(
        InlineKeyboardButton(text="💾 Backup", callback_data="admin:backup"),
    )

    return builder.as_markup()


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin paneliga qaytish"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Admin panelga qaytish", callback_data="admin:panel")
    )
    return builder.as_markup()


def get_favorites_keyboard(
    animes: list[Anime],
) -> InlineKeyboardMarkup:
    """Sevimlilar ro'yxati klaviaturasi"""
    builder = InlineKeyboardBuilder()

    for anime in animes:
        builder.row(
            InlineKeyboardButton(
                text=f"❤️ #{anime.code} | {anime.name}",
                callback_data=f"anime:{anime.id}",
            )
        )

    if not animes:
        builder.row(
            InlineKeyboardButton(
                text="📋 Animelar ro'yxatiga o'tish",
                callback_data="anime_list:1",
            )
        )

    return builder.as_markup()


def get_edit_anime_fields_keyboard() -> InlineKeyboardMarkup:
    """Anime tahrirlash maydonlari"""
    builder = InlineKeyboardBuilder()

    fields = [
        ("📝 Nomi", "name"),
        ("📖 Tavsif", "description"),
        ("🎭 Janr", "genre"),
        ("📅 Yili", "year"),
        ("⏱ Davomiyligi", "duration"),
        ("🌐 Tili", "language"),
        ("⭐ Reyting", "rating"),
        ("📺 Holati", "status"),
    ]

    for i in range(0, len(fields), 2):
        row = []
        for label, field in fields[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"edit_field:{field}",
                )
            )
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:panel")
    )

    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Broadcast tasdiqlash"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast:cancel"),
    )
    return builder.as_markup()


def get_search_result_keyboard(
    animes: list[Anime],
) -> InlineKeyboardMarkup:
    """Qidiruv natijalari klaviaturasi"""
    builder = InlineKeyboardBuilder()

    for anime in animes:
        builder.row(
            InlineKeyboardButton(
                text=f"#{anime.code} | {anime.name}",
                callback_data=f"anime:{anime.id}",
            )
        )

    return builder.as_markup()


def get_noop_keyboard() -> InlineKeyboardMarkup:
    """Bo'sh inline klaviatura"""
    return InlineKeyboardMarkup(inline_keyboard=[])
