"""
handlers/user.py - Foydalanuvchi handlerlari
=============================================
Start, help, anime ro'yxati, sevimlilar va boshqa
foydalanuvchi funksiyalari.
"""

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
    Message,
    PhotoSize,
)
from loguru import logger

from bot.config import (
    ADMIN_IDS,
    ANIME_PER_PAGE,
    CHANNEL_ID,
    CHANNEL_USERNAME,
    IMAGES_DIR,
    START_MESSAGE,
    HELP_MESSAGE,
    SUBSCRIPTION_MESSAGE,
)
from bot.database import crud
from bot.database.models import User
from bot.keyboards.inline import (
    get_anime_detail_keyboard,
    get_anime_list_keyboard,
    get_favorites_keyboard,
    get_subscription_keyboard,
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_keyboard
from bot.states import SearchState
from bot.utils import (
    check_subscription,
    format_anime_info,
    search_anime_by_image,
    format_image_search_results,
)

router = Router(name="user")


# ==========================================
# OBUNA TEKSHIRISH
# ==========================================

async def require_subscription(message: Message, session) -> bool:
    """
    Foydalanuvchi kanalga obuna bo'lganligini tekshiradi.
    Obuna bo'lmagan bo'lsa, xabar yuboradi va False qaytaradi.
    """
    if not CHANNEL_ID or CHANNEL_ID == "-1001234567890":
        return True

    is_subscribed = await check_subscription(message.bot, message.from_user.id, CHANNEL_ID)

    if not is_subscribed:
        channel = CHANNEL_USERNAME or CHANNEL_ID
        await message.answer(
            SUBSCRIPTION_MESSAGE.format(channel=channel),
            reply_markup=get_subscription_keyboard(),
        )
        # DB da yangilash
        await crud.update_user_subscription(session, message.from_user.id, False)
        return False

    # DB da yangilash
    await crud.update_user_subscription(session, message.from_user.id, True)
    return True


# ==========================================
# START
# ==========================================

@router.message(CommandStart())
async def cmd_start(message: Message, session, db_user: User, state: FSMContext) -> None:
    """Bot ishga tushirilganda"""
    await state.clear()

    # Obuna tekshirish
    if not await require_subscription(message, session):
        return

    # Poster yuborish (agar mavjud bo'lsa)
    poster_path = IMAGES_DIR / "start_poster.jpg"

    caption = START_MESSAGE.format(name=message.from_user.first_name)

    if poster_path.exists():
        try:
            await message.answer_photo(
                photo=FSInputFile(str(poster_path)),
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )
        except Exception:
            await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )
    else:
        # Poster yo'q — faqat matn
        start_text = f"🎌 <b>Anime Bot ga xush kelibsiz!</b>\n\n👋 Salom, <b>{message.from_user.first_name}</b>!\n\n" \
                     f"📺 Anime tomosha qilish va yuklab olish imkoniyati mavjud!\n\n" \
                     f"🔍 Quyidagi tugmalardan foydalaning:"
        await message.answer(
            start_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )

    logger.info(f"▶️ /start | {message.from_user.id} - {message.from_user.full_name}")


# ==========================================
# HELP
# ==========================================

@router.message(F.text == "📚 Qo'llanma")
@router.message(Command("help"))
async def cmd_help(message: Message, session, db_user: User, state: FSMContext) -> None:
    """Yordam xabari"""
    await state.clear()

    if not await require_subscription(message, session):
        return

    await message.answer(
        HELP_MESSAGE,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


# ==========================================
# OBUNA TEKSHIRISH CALLBACK
# ==========================================

@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, session) -> None:
    """Obuna tekshirish tugmasi"""
    is_subscribed = await check_subscription(
        callback.bot, callback.from_user.id, CHANNEL_ID
    )

    if is_subscribed:
        await crud.update_user_subscription(session, callback.from_user.id, True)
        await callback.message.delete()
        await callback.message.answer(
            "✅ <b>Tabriklaymiz! Obuna tasdiqlandi.</b>\n\nEndi botdan to'liq foydalanishingiz mumkin!",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )
        await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    else:
        channel = CHANNEL_USERNAME or CHANNEL_ID
        await callback.answer(
            f"❌ Siz hali {channel} kanaliga obuna bo'lmagansiz!",
            show_alert=True,
        )


# ==========================================
# KOD ORQALI QIDIRUV
# ==========================================

@router.message(F.text == "🆔 Kod orqali qidiruv")
async def search_by_code_start(message: Message, state: FSMContext) -> None:
    """Kod orqali qidiruv boshlash"""
    await state.set_state(SearchState.waiting_for_code)
    await message.answer(
        "🔍 <b>Anime kodini kiriting:</b>\n\n"
        "Masalan: <code>1</code>, <code>2</code>, <code>15</code>\n\n"
        "<i>💡 Barcha animelar kodlarini ko'rish uchun 📋 Ro'yxat tugmasini bosing.</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(SearchState.waiting_for_code, F.text)
async def process_code_search(
    message: Message, session, db_user: User, state: FSMContext
) -> None:
    """Anime kodi qayta ishlash"""
    text = message.text.strip()

    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Qidiruv bekor qilindi.",
            reply_markup=get_main_keyboard(),
        )
        return

    if not text.isdigit():
        await message.answer(
            "❌ <b>Faqat raqam kiriting!</b>\n\nMasalan: <code>1</code>",
            parse_mode="HTML",
        )
        return

    code = int(text)
    await state.clear()

    await _send_anime_by_code(message, session, db_user, code)


async def _send_anime_by_code(
    message: Message, session, db_user: User, code: int
) -> None:
    """Anime kodini topib yuborish (ichki funksiya)"""
    anime = await crud.get_anime_by_code(session, code)

    if not anime:
        await message.answer(
            f"❌ <b>{code} kodli anime topilmadi!</b>\n\n"
            f"📋 Mavjud animelarni ko'rish uchun <b>📋 Ro'yxat</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )
        # Qidiruv tarixiga qo'shish
        if db_user:
            await crud.add_search_history(session, db_user.id, str(code), found=False)
            await crud.increment_user_searches(session, message.from_user.id)
        return

    # Statistika yangilash
    await crud.increment_anime_searches(session, anime.id)
    if db_user:
        await crud.add_search_history(session, db_user.id, str(code), anime.code, found=True)
        await crud.increment_user_searches(session, message.from_user.id)

    # Sevimlilar tekshirish
    is_fav = False
    if db_user:
        is_fav = await crud.is_favorite(session, db_user.id, anime.id)

    caption = format_anime_info(anime)
    keyboard = get_anime_detail_keyboard(anime, is_favorite=is_fav)

    if anime.poster_file_id:
        try:
            await message.answer_photo(
                photo=anime.poster_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.warning(f"Poster yuborishda xato: {e}")
            await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


# ==========================================
# RAQAM YOZILGANDA QIDIRUV
# ==========================================

@router.message(F.text.regexp(r"^\d+$"))
async def search_by_number(message: Message, session, db_user: User) -> None:
    """Foydalanuvchi to'g'ridan-to'g'ri raqam yozsa"""
    code = int(message.text.strip())
    await _send_anime_by_code(message, session, db_user, code)


# ==========================================
# ANIME RO'YXATI
# ==========================================

@router.message(F.text.in_(["🎬 Anime", "📋 Ro'yxat"]))
async def show_anime_list(message: Message, session, db_user: User, state: FSMContext) -> None:
    """Animelar ro'yxatini chiqarish"""
    await state.clear()

    if not await require_subscription(message, session):
        return

    animes, total = await crud.get_animes_paginated(session, page=1, per_page=ANIME_PER_PAGE)

    if not animes:
        await message.answer(
            "📭 <b>Hozircha birorta ham anime mavjud emas.</b>\n\n"
            "Tez orada yangi animelar qo'shiladi! 🎌",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )
        return

    import math
    total_pages = max(1, math.ceil(total / ANIME_PER_PAGE))

    header = (
        f"🎬 <b>Barcha Animelar</b>\n"
        f"📊 Jami: <b>{total}</b> ta | Sahifa: <b>1/{total_pages}</b>\n\n"
        f"Anime tanlash uchun pastdagi tugmalardan bosing:"
    )

    await message.answer(
        header,
        parse_mode="HTML",
        reply_markup=get_anime_list_keyboard(animes, page=1, total=total),
    )


@router.callback_query(F.data.startswith("anime_list:"))
async def anime_list_page(callback: CallbackQuery, session) -> None:
    """Animelar ro'yxati pagination"""
    page = int(callback.data.split(":")[1])

    animes, total = await crud.get_animes_paginated(session, page=page, per_page=ANIME_PER_PAGE)

    import math
    total_pages = max(1, math.ceil(total / ANIME_PER_PAGE))

    header = (
        f"🎬 <b>Barcha Animelar</b>\n"
        f"📊 Jami: <b>{total}</b> ta | Sahifa: <b>{page}/{total_pages}</b>\n\n"
        f"Anime tanlash uchun pastdagi tugmalardan bosing:"
    )

    try:
        await callback.message.edit_text(
            header,
            parse_mode="HTML",
            reply_markup=get_anime_list_keyboard(animes, page=page, total=total),
        )
    except Exception:
        pass

    await callback.answer()


# ==========================================
# ANIME TAFSILOTI (CALLBACK)
# ==========================================

@router.callback_query(F.data.startswith("anime:"))
async def show_anime_detail(callback: CallbackQuery, session, db_user: User) -> None:
    """Anime tafsilotini ko'rsatish"""
    anime_id = int(callback.data.split(":")[1])

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    # Statistika
    await crud.increment_anime_views(session, anime.id)

    # Sevimlilar
    is_fav = False
    if db_user:
        is_fav = await crud.is_favorite(session, db_user.id, anime.id)

    caption = format_anime_info(anime)
    keyboard = get_anime_detail_keyboard(anime, is_favorite=is_fav)

    try:
        if anime.poster_file_id:
            await callback.message.answer_photo(
                photo=anime.poster_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            await callback.message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    except Exception as e:
        logger.error(f"Anime tafsilotida xato: {e}")

    await callback.answer()


@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery, session) -> None:
    """Ro'yxatga qaytish"""
    animes, total = await crud.get_animes_paginated(session, page=1, per_page=ANIME_PER_PAGE)

    import math
    total_pages = max(1, math.ceil(total / ANIME_PER_PAGE))

    header = (
        f"🎬 <b>Barcha Animelar</b>\n"
        f"📊 Jami: <b>{total}</b> ta | Sahifa: <b>1/{total_pages}</b>"
    )

    try:
        await callback.message.edit_text(
            header,
            parse_mode="HTML",
            reply_markup=get_anime_list_keyboard(animes, page=1, total=total),
        )
    except Exception:
        await callback.message.answer(
            header,
            parse_mode="HTML",
            reply_markup=get_anime_list_keyboard(animes, page=1, total=total),
        )

    await callback.answer()


# ==========================================
# TOMOSHA QILISH
# ==========================================

@router.callback_query(F.data.startswith("watch:"))
async def show_watch_episodes(callback: CallbackQuery, session) -> None:
    """Tomosha qilish — qismlar ro'yxati"""
    anime_id = int(callback.data.split(":")[1])

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    episodes = await crud.get_episodes_by_anime(session, anime_id)

    if not episodes:
        await callback.answer(
            "⚠️ Bu anime uchun hali qism qo'shilmagan!", show_alert=True
        )
        return

    from bot.keyboards.inline import get_episodes_keyboard
    await callback.message.answer(
        f"🎬 <b>{anime.name}</b> — Qismni tanlang:\n\n"
        f"📺 Jami: <b>{len(episodes)}</b> ta qism",
        parse_mode="HTML",
        reply_markup=get_episodes_keyboard(anime, episodes, action="watch"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ep_watch:"))
async def stream_episode(callback: CallbackQuery, session) -> None:
    """Qismni streaming sifatida yuborish"""
    parts = callback.data.split(":")
    anime_id = int(parts[1])
    ep_num = int(parts[2])

    episode = await crud.get_episode(session, anime_id, ep_num)
    if not episode:
        await callback.answer("❌ Qism topilmadi!", show_alert=True)
        return

    anime = await crud.get_anime_by_id(session, anime_id)
    ep_title = f"{ep_num}-qism"
    if episode.title:
        ep_title += f" — {episode.title}"

    try:
        await callback.message.answer_video(
            video=episode.file_id,
            caption=(
                f"🎬 <b>{anime.name if anime else 'Anime'}</b>\n"
                f"▶️ <b>{ep_title}</b>\n\n"
                f"<i>📺 Streaming rejimida tomosha qiling</i>"
            ),
            parse_mode="HTML",
            supports_streaming=True,
        )
        await crud.increment_episode_views(session, episode.id)
        await callback.answer()
    except Exception as e:
        logger.error(f"Video yuborishda xato: {e}")
        await callback.answer(
            "❌ Video yuborishda xato. Keyinroq urinib ko'ring.", show_alert=True
        )


# ==========================================
# YUKLAB OLISH
# ==========================================

@router.callback_query(F.data.startswith("download:"))
async def show_download_episodes(callback: CallbackQuery, session) -> None:
    """Yuklab olish — qismlar ro'yxati"""
    anime_id = int(callback.data.split(":")[1])

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    episodes = await crud.get_episodes_by_anime(session, anime_id)

    if not episodes:
        await callback.answer(
            "⚠️ Bu anime uchun hali qism qo'shilmagan!", show_alert=True
        )
        return

    from bot.keyboards.inline import get_episodes_keyboard
    await callback.message.answer(
        f"📥 <b>{anime.name}</b> — Qismni tanlang:\n\n"
        f"🎞 Jami: <b>{len(episodes)}</b> ta qism",
        parse_mode="HTML",
        reply_markup=get_episodes_keyboard(anime, episodes, action="download"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ep_download:"))
async def download_episode(callback: CallbackQuery, session) -> None:
    """Qismni yuklab olish sifatida yuborish"""
    parts = callback.data.split(":")
    anime_id = int(parts[1])
    ep_num = int(parts[2])

    episode = await crud.get_episode(session, anime_id, ep_num)
    if not episode:
        await callback.answer("❌ Qism topilmadi!", show_alert=True)
        return

    anime = await crud.get_anime_by_id(session, anime_id)
    ep_title = f"{ep_num}-qism"
    if episode.title:
        ep_title += f" — {episode.title}"

    try:
        await callback.message.answer_document(
            document=episode.file_id,
            caption=(
                f"📥 <b>{anime.name if anime else 'Anime'}</b>\n"
                f"🎞 <b>{ep_title}</b>\n\n"
                f"<i>✅ Yuklash tayyor!</i>"
            ),
            parse_mode="HTML",
        )
        await crud.increment_episode_downloads(session, episode.id)
        await callback.answer("✅ Yuklash boshlandi!")
    except Exception as e:
        logger.error(f"Download xato: {e}")
        await callback.answer(
            "❌ Xato. Keyinroq urinib ko'ring.", show_alert=True
        )


# ==========================================
# QISM SAHIFALASH
# ==========================================

@router.callback_query(F.data.startswith("ep_page:"))
async def episode_page(callback: CallbackQuery, session) -> None:
    """Qismlar pagination"""
    parts = callback.data.split(":")
    action = parts[1]
    anime_id = int(parts[2])
    page = int(parts[3])

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    episodes = await crud.get_episodes_by_anime(session, anime_id)

    from bot.keyboards.inline import get_episodes_keyboard
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_episodes_keyboard(anime, episodes, action=action, page=page)
        )
    except Exception:
        pass
    await callback.answer()


# ==========================================
# SEVIMLILARGA QO'SHISH
# ==========================================

@router.callback_query(F.data.startswith("fav:"))
async def add_to_favorites(callback: CallbackQuery, session, db_user: User) -> None:
    """Sevimlilarga qo'shish"""
    anime_id = int(callback.data.split(":")[1])

    if not db_user:
        await callback.answer("❌ Iltimos, /start bosing!", show_alert=True)
        return

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    _, created = await crud.add_favorite(session, db_user.id, anime_id)

    if created:
        await callback.answer("❤️ Sevimlilarga qo'shildi!", show_alert=True)
    else:
        await callback.answer("⚠️ Bu anime allaqachon sevimlilaringizda!", show_alert=True)

    # Klaviaturani yangilash
    is_fav = True
    keyboard = get_anime_detail_keyboard(anime, is_favorite=is_fav)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


@router.callback_query(F.data.startswith("unfav:"))
async def remove_from_favorites(callback: CallbackQuery, session, db_user: User) -> None:
    """Sevimlilardan olib tashlash"""
    anime_id = int(callback.data.split(":")[1])

    if not db_user:
        await callback.answer("❌ Iltimos, /start bosing!", show_alert=True)
        return

    anime = await crud.get_anime_by_id(session, anime_id)
    if not anime:
        await callback.answer("❌ Anime topilmadi!", show_alert=True)
        return

    removed = await crud.remove_favorite(session, db_user.id, anime_id)

    if removed:
        await callback.answer("💔 Sevimlilardan olib tashlandi!", show_alert=True)
    else:
        await callback.answer("⚠️ Bu anime sevimlilaringizda yo'q!", show_alert=True)

    # Klaviaturani yangilash
    keyboard = get_anime_detail_keyboard(anime, is_favorite=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


# ==========================================
# RASM ORQALI QIDIRUV
# ==========================================

@router.message(F.text == "🖼 Rasm orqali qidiruv")
async def image_search_start(message: Message, state: FSMContext) -> None:
    """Rasm orqali qidiruv boshlash"""
    await state.set_state(SearchState.waiting_for_image)
    await message.answer(
        "🖼 <b>Anime posteri yoki skrinshot yuboring:</b>\n\n"
        "<i>💡 Anime sahna rasmi yoki poster yuborish orqali anime nomini topishimiz mumkin.</i>\n\n"
        "❌ Bekor qilish uchun /start bosing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(SearchState.waiting_for_image, F.photo)
async def process_image_search(
    message: Message, session, db_user: User, state: FSMContext
) -> None:
    """Rasm orqali qidiruv"""
    await state.clear()

    processing_msg = await message.answer("🔄 <b>Rasm tahlil qilinmoqda...</b>", parse_mode="HTML")

    # Rasmning eng katta versiyasini olish
    photo: PhotoSize = message.photo[-1]

    try:
        # Faylni yuklab olish
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)

        # API ga yuborish
        results = await search_anime_by_image(file_bytes.read())

        await processing_msg.delete()

        if results:
            result_text = format_image_search_results(results)
            await message.answer(
                result_text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )
        else:
            await message.answer(
                "❌ <b>Anime topilmadi.</b>\n\n"
                "Boshqa rasm yuboring yoki kod orqali qidiring.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(),
            )

    except Exception as e:
        logger.error(f"Rasm qidiruvda xato: {e}")
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await message.answer(
            "❌ Rasm qidiruvda xato yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=get_main_keyboard(),
        )


# ==========================================
# REKLAMA (KANAL HAQIDA)
# ==========================================

@router.message(F.text == "📢 Reklama")
async def show_ad_info(message: Message) -> None:
    """Reklama ma'lumoti"""
    channel = CHANNEL_USERNAME or "@your_channel"
    await message.answer(
        f"📢 <b>Reklama va hamkorlik</b>\n\n"
        f"🤝 Bot yoki kanalimizda reklama joylash uchun:\n"
        f"👤 Admin bilan bog'laning: {channel}\n\n"
        f"📊 Botimiz statistikasi:\n"
        f"• Har kuni faol foydalanuvchilar mavjud\n"
        f"• Premium anime kontenti\n"
        f"• Tez javob beruvchi bot",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


# ==========================================
# NOOP CALLBACK
# ==========================================

@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    """Bo'sh callback"""
    await callback.answer()
