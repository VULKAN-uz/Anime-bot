"""
handlers/admin.py - Admin handlerlari (1/2)
Admin panel, anime qo'shish, tahrirlash, o'chirish.
"""
import asyncio
from datetime import datetime
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import ADMIN_IDS
from bot.database import crud
from bot.filters import IsAdmin
from bot.keyboards.inline import get_admin_panel_keyboard, get_back_to_admin_keyboard, get_edit_anime_fields_keyboard, get_broadcast_confirm_keyboard
from bot.keyboards.reply import (
    get_admin_main_keyboard, get_cancel_keyboard, get_confirmation_keyboard,
    get_main_keyboard, get_more_episodes_keyboard, get_skip_cancel_keyboard,
    get_status_keyboard, remove_keyboard
)
from bot.states import (
    AddAnimeState, AddEpisodeState, BroadcastState,
    ChangePosterState, DeleteAnimeState, DeleteEpisodeState, EditAnimeState
)
from bot.utils import create_backup, format_stats, get_backup_list

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_cancel(text: str) -> bool:
    return text in ("❌ Bekor qilish", "❌ Yo'q, bekor", "/cancel")


async def _send_admin_panel(message: Message, session) -> None:
    stats = await crud.get_full_stats(session)
    from bot.config import ADMIN_PANEL_MESSAGE
    text = ADMIN_PANEL_MESSAGE.format(
        name=message.from_user.full_name,
        user_id=message.from_user.id,
        users=stats["users_count"],
        animes=stats["animes_count"],
        videos=stats["videos_count"],
        searches=stats["searches_count"],
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())


# ── /admin ───────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, session, state: FSMContext) -> None:
    await state.clear()
    await _send_admin_panel(message, session)


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_keyboard())


# ── STATISTIKA ───────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message, session) -> None:
    stats = await crud.get_full_stats(session)
    await message.answer(format_stats(stats), parse_mode="HTML", reply_markup=get_admin_main_keyboard())


@router.message(F.text == "👤 Foydalanuvchilar")
async def show_users(message: Message, session) -> None:
    stats = await crud.get_full_stats(session)
    text = (
        f"👥 <b>Foydalanuvchilar</b>\n\n"
        f"• Jami: <b>{stats['users_count']}</b>\n"
        f"• Bugungi yangilar: <b>{stats['today_users']}</b>\n"
        f"• 24 soat ichida faol: <b>{stats['active_users']}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())


# ── ANIME QO'SHISH ────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Anime qo'shish")
async def add_anime_start(message: Message, session, state: FSMContext) -> None:
    await state.clear()
    next_code = await crud.get_next_anime_code(session)
    await state.set_state(AddAnimeState.waiting_for_code)
    await state.update_data(suggested_code=next_code)
    await message.answer(
        f"➕ <b>Yangi anime qo'shish</b>\n\n"
        f"<b>1. Anime kodini kiriting:</b>\n"
        f"💡 Tavsiya etilgan kod: <code>{next_code}</code>\n\n"
        f"(Boshqa kod kiritsangiz ham bo'ladi)",
        parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )


@router.message(AddAnimeState.waiting_for_code)
async def add_anime_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text):
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit():
        return await message.answer("❌ Faqat raqam kiriting!")
    code = int(message.text.strip())
    existing = await crud.get_anime_by_code(session, code)
    if existing:
        return await message.answer(f"❌ <b>{code}</b> kodli anime allaqachon mavjud!", parse_mode="HTML")
    await state.update_data(code=code)
    await state.set_state(AddAnimeState.waiting_for_name)
    await message.answer("✅ Kod qabul qilindi.\n\n<b>2. Anime nomini kiriting:</b>", parse_mode="HTML")


@router.message(AddAnimeState.waiting_for_name)
async def add_anime_name(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text):
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_main_keyboard())
    await state.update_data(name=message.text.strip())
    await state.set_state(AddAnimeState.waiting_for_poster)
    await message.answer(
        "✅ Nom qabul qilindi.\n\n<b>3. Anime posterini yuboring:</b>\n<i>(Rasm yuboring yoki o'tkazib yuboring)</i>",
        parse_mode="HTML", reply_markup=get_skip_cancel_keyboard()
    )


@router.message(AddAnimeState.waiting_for_poster)
async def add_anime_poster(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text):
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_main_keyboard())
    poster_file_id = None
    if message.photo:
        poster_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == "⏭ O'tkazib yuborish":
        poster_file_id = None
    await state.update_data(poster_file_id=poster_file_id)
    await state.set_state(AddAnimeState.waiting_for_description)
    await message.answer(
        "✅ Poster qabul qilindi.\n\n<b>4. Tavsif kiriting:</b>",
        parse_mode="HTML", reply_markup=get_skip_cancel_keyboard()
    )


@router.message(AddAnimeState.waiting_for_description)
async def add_anime_desc(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    desc = None if message.text.strip() == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddAnimeState.waiting_for_genre)
    await message.answer("<b>5. Janrini kiriting:</b>\n<i>Masalan: Aksyon, Sarguzasht, Drama</i>", parse_mode="HTML", reply_markup=get_skip_cancel_keyboard())


@router.message(AddAnimeState.waiting_for_genre)
async def add_anime_genre(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    genre = None if message.text.strip() == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddAnimeState.waiting_for_year)
    await message.answer("<b>6. Chiqgan yilini kiriting:</b>\n<i>Masalan: 2023</i>", parse_mode="HTML", reply_markup=get_skip_cancel_keyboard())


@router.message(AddAnimeState.waiting_for_year)
async def add_anime_year(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    year = None
    t = message.text.strip()
    if t != "⏭ O'tkazib yuborish":
        if not t.isdigit(): return await message.answer("❌ Faqat raqam!")
        year = int(t)
    await state.update_data(year=year)
    await state.set_state(AddAnimeState.waiting_for_duration)
    await message.answer("<b>7. Davomiyligini kiriting:</b>\n<i>Masalan: 24 daqiqa</i>", parse_mode="HTML", reply_markup=get_skip_cancel_keyboard())


@router.message(AddAnimeState.waiting_for_duration)
async def add_anime_duration(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    dur = None if message.text.strip() == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(duration=dur)
    await state.set_state(AddAnimeState.waiting_for_language)
    await message.answer("<b>8. Tilini kiriting:</b>\n<i>Masalan: O'zbek tilida, Rus tilida</i>", parse_mode="HTML", reply_markup=get_skip_cancel_keyboard())


@router.message(AddAnimeState.waiting_for_language)
async def add_anime_lang(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    lang = None if message.text.strip() == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(language=lang)
    await state.set_state(AddAnimeState.waiting_for_rating)
    await message.answer("<b>9. Reytingini kiriting:</b>\n<i>0.0 — 10.0, masalan: 8.5</i>", parse_mode="HTML", reply_markup=get_skip_cancel_keyboard())


@router.message(AddAnimeState.waiting_for_rating)
async def add_anime_rating(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    rating = None
    t = message.text.strip()
    if t != "⏭ O'tkazib yuborish":
        try:
            rating = float(t.replace(",", "."))
            if not 0 <= rating <= 10: return await message.answer("❌ 0 dan 10 gacha kiriting!")
        except ValueError:
            return await message.answer("❌ Noto'g'ri format!")
    await state.update_data(rating=rating)
    await state.set_state(AddAnimeState.waiting_for_status)
    await message.answer("<b>10. Holatini tanlang:</b>", parse_mode="HTML", reply_markup=get_status_keyboard())


@router.message(AddAnimeState.waiting_for_status)
async def add_anime_status(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    status_map = {"📺 ongoing": "ongoing", "✅ completed": "completed", "⏸ paused": "paused"}
    status = status_map.get(message.text.strip(), "ongoing")
    await state.update_data(status=status)
    data = await state.get_data()

    # Tasdiqlash
    confirm_text = (
        f"✅ <b>Animeni saqlashni tasdiqlang:</b>\n\n"
        f"🆔 Kod: <code>{data.get('code')}</code>\n"
        f"📝 Nom: <b>{data.get('name')}</b>\n"
        f"📖 Tavsif: {data.get('description') or '—'}\n"
        f"🎭 Janr: {data.get('genre') or '—'}\n"
        f"📅 Yil: {data.get('year') or '—'}\n"
        f"⏱ Davomiyligi: {data.get('duration') or '—'}\n"
        f"🌐 Til: {data.get('language') or '—'}\n"
        f"⭐ Reyting: {data.get('rating') or '—'}\n"
        f"📺 Holat: {status}\n"
        f"🖼 Poster: {'✅' if data.get('poster_file_id') else '❌'}"
    )
    await state.set_state(AddAnimeState.waiting_for_confirmation)
    await message.answer(confirm_text, parse_mode="HTML", reply_markup=get_confirmation_keyboard())


@router.message(AddAnimeState.waiting_for_confirmation)
async def add_anime_confirm(message: Message, session, state: FSMContext) -> None:
    if message.text.strip() != "✅ Ha, tasdiqlash":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.", reply_markup=get_admin_main_keyboard())
    data = await state.get_data()
    await state.clear()
    try:
        anime = await crud.create_anime(
            session,
            code=data["code"], name=data["name"],
            description=data.get("description"), genre=data.get("genre"),
            year=data.get("year"), duration=data.get("duration"),
            language=data.get("language"), rating=data.get("rating"),
            poster_file_id=data.get("poster_file_id"), status=data.get("status", "ongoing"),
        )
        await session.commit()
        await message.answer(
            f"✅ <b>Anime muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🆔 Kod: <code>{anime.code}</code>\n"
            f"📝 Nom: <b>{anime.name}</b>\n\n"
            f"Endi qism qo'shish uchun <b>🎬 Qism qo'shish</b> tugmasini bosing.",
            parse_mode="HTML", reply_markup=get_admin_main_keyboard()
        )
        logger.info(f"✅ Admin {message.from_user.id} anime qo'shdi: {anime.code} - {anime.name}")
    except Exception as e:
        logger.error(f"Anime qo'shishda xato: {e}")
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_main_keyboard())


# ── QISM QO'SHISH ─────────────────────────────────────────────────────────────

@router.message(F.text == "🎬 Qism qo'shish")
async def add_episode_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddEpisodeState.waiting_for_anime_code)
    await message.answer(
        "🎬 <b>Qism qo'shish</b>\n\n<b>Anime kodini kiriting:</b>",
        parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )


@router.message(AddEpisodeState.waiting_for_anime_code)
async def add_ep_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Faqat raqam!")
    code = int(message.text.strip())
    anime = await crud.get_anime_by_code(session, code)
    if not anime: return await message.answer(f"❌ <b>{code}</b> kodli anime topilmadi!", parse_mode="HTML")
    episodes = await crud.get_episodes_by_anime(session, anime.id)
    next_ep = (max((e.episode_number for e in episodes), default=0) + 1) if episodes else 1
    await state.update_data(anime_id=anime.id, anime_name=anime.name, next_ep=next_ep)
    await state.set_state(AddEpisodeState.waiting_for_episode_number)
    await message.answer(
        f"✅ Anime: <b>{anime.name}</b>\n\n<b>Qism raqamini kiriting:</b>\n💡 Tavsiya: <code>{next_ep}</code>",
        parse_mode="HTML"
    )


@router.message(AddEpisodeState.waiting_for_episode_number)
async def add_ep_number(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Faqat raqam!")
    ep_num = int(message.text.strip())
    data = await state.get_data()
    existing = await crud.get_episode(session, data["anime_id"], ep_num)
    if existing: return await message.answer(f"❌ {ep_num}-qism allaqachon mavjud!")
    await state.update_data(episode_number=ep_num)
    await state.set_state(AddEpisodeState.waiting_for_video)
    await message.answer(
        f"✅ Qism raqami: <b>{ep_num}</b>\n\n📹 <b>Video faylni yuboring:</b>",
        parse_mode="HTML"
    )


@router.message(AddEpisodeState.waiting_for_video, F.video | F.document)
async def add_ep_video(message: Message, session, state: FSMContext) -> None:
    data = await state.get_data()
    if message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        duration = message.video.duration
        file_size = message.video.file_size
    else:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        duration = None
        file_size = message.document.file_size

    try:
        ep = await crud.create_episode(
            session,
            anime_id=data["anime_id"],
            episode_number=data["episode_number"],
            file_id=file_id,
            file_unique_id=file_unique_id,
            duration=duration,
            file_size=file_size,
        )
        await session.commit()
        next_ep = data["episode_number"] + 1
        await state.update_data(episode_number=next_ep, next_ep=next_ep)
        await state.set_state(AddEpisodeState.waiting_for_more)
        await message.answer(
            f"✅ <b>{data['episode_number']}-qism muvaffaqiyatli qo'shildi!</b>\n\n"
            f"➕ Yana qism qo'shish yoki tugatish?",
            parse_mode="HTML", reply_markup=get_more_episodes_keyboard()
        )
        logger.info(f"🎞 Qism qo'shildi: anime_id={data['anime_id']}, ep={data['episode_number']}")
    except Exception as e:
        logger.error(f"Qism qo'shishda xato: {e}")
        await message.answer(f"❌ Xato: {e}")


@router.message(AddEpisodeState.waiting_for_more)
async def add_ep_more(message: Message, state: FSMContext) -> None:
    t = message.text.strip()
    if t == "✅ Tugatish" or _is_cancel(t):
        await state.clear()
        return await message.answer("✅ Qism qo'shish yakunlandi!", reply_markup=get_admin_main_keyboard())
    if t == "➕ Yana qism qo'shish":
        data = await state.get_data()
        await state.set_state(AddEpisodeState.waiting_for_video)
        return await message.answer(
            f"📹 <b>{data.get('episode_number', '?')}-qism videosini yuboring:</b>",
            parse_mode="HTML"
        )


# ── QISM O'CHIRISH ────────────────────────────────────────────────────────────

@router.message(F.text == "❌ Qism o'chirish")
async def del_episode_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(DeleteEpisodeState.waiting_for_anime_code)
    await message.answer("🗑 <b>Qism o'chirish</b>\n\n<b>Anime kodini kiriting:</b>", parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(DeleteEpisodeState.waiting_for_anime_code)
async def del_ep_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Raqam kiriting!")
    code = int(message.text.strip())
    anime = await crud.get_anime_by_code(session, code)
    if not anime: return await message.answer(f"❌ {code} kodli anime topilmadi!")
    episodes = await crud.get_episodes_by_anime(session, anime.id)
    if not episodes: return await message.answer("❌ Bu animeda qism yo'q!")
    ep_list = ", ".join(str(e.episode_number) for e in episodes)
    await state.update_data(anime_id=anime.id, anime_name=anime.name)
    await state.set_state(DeleteEpisodeState.waiting_for_episode_number)
    await message.answer(f"✅ Anime: <b>{anime.name}</b>\n\nMavjud qismlar: <code>{ep_list}</code>\n\n<b>O'chiriladigan qism raqamini kiriting:</b>", parse_mode="HTML")


@router.message(DeleteEpisodeState.waiting_for_episode_number)
async def del_ep_number(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Raqam kiriting!")
    ep_num = int(message.text.strip())
    data = await state.get_data()
    ep = await crud.get_episode(session, data["anime_id"], ep_num)
    if not ep: return await message.answer(f"❌ {ep_num}-qism topilmadi!")
    await state.update_data(episode_number=ep_num)
    await state.set_state(DeleteEpisodeState.waiting_for_confirmation)
    await message.answer(
        f"⚠️ <b>{data['anime_name']}</b> — <b>{ep_num}-qism</b> o'chirilsinmi?",
        parse_mode="HTML", reply_markup=get_confirmation_keyboard()
    )


@router.message(DeleteEpisodeState.waiting_for_confirmation)
async def del_ep_confirm(message: Message, session, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    if message.text.strip() != "✅ Ha, tasdiqlash":
        return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    deleted = await crud.delete_episode(session, data["anime_id"], data["episode_number"])
    await session.commit()
    if deleted:
        await message.answer(f"✅ {data['episode_number']}-qism o'chirildi!", reply_markup=get_admin_main_keyboard())
    else:
        await message.answer("❌ O'chirishda xato!", reply_markup=get_admin_main_keyboard())


# ── ANIME TAHRIRLASH ──────────────────────────────────────────────────────────

@router.message(F.text == "✏️ Anime tahrirlash")
async def edit_anime_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(EditAnimeState.waiting_for_anime_code)
    await message.answer("✏️ <b>Anime tahrirlash</b>\n\n<b>Anime kodini kiriting:</b>", parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(EditAnimeState.waiting_for_anime_code)
async def edit_anime_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Raqam kiriting!")
    code = int(message.text.strip())
    anime = await crud.get_anime_by_code(session, code)
    if not anime: return await message.answer(f"❌ {code} kodli anime topilmadi!")
    await state.update_data(anime_id=anime.id, anime_name=anime.name)
    await state.set_state(EditAnimeState.waiting_for_field)
    await message.answer(
        f"✅ Anime: <b>{anime.name}</b>\n\n<b>Qaysi maydonni tahrirlaysiz?</b>",
        parse_mode="HTML", reply_markup=remove_keyboard
    )
    await message.answer("Maydonni tanlang:", reply_markup=get_edit_anime_fields_keyboard())


@router.callback_query(EditAnimeState.waiting_for_field, F.data.startswith("edit_field:"))
async def edit_field_selected(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    field_names = {
        "name": "Nomi", "description": "Tavsif", "genre": "Janr",
        "year": "Yili", "duration": "Davomiyligi", "language": "Tili",
        "rating": "Reyting", "status": "Holat"
    }
    await state.update_data(edit_field=field)
    await state.set_state(EditAnimeState.waiting_for_value)
    await callback.message.answer(
        f"✏️ <b>{field_names.get(field, field)}</b> uchun yangi qiymat kiriting:",
        parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(EditAnimeState.waiting_for_value)
async def edit_value_save(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    data = await state.get_data()
    field = data["edit_field"]
    value = message.text.strip()
    update_data = {}
    if field == "year":
        if not value.isdigit(): return await message.answer("❌ Raqam kiriting!")
        update_data[field] = int(value)
    elif field == "rating":
        try: update_data[field] = float(value.replace(",", "."))
        except: return await message.answer("❌ Noto'g'ri format!")
    else:
        update_data[field] = value
    await state.clear()
    await crud.update_anime(session, data["anime_id"], **update_data)
    await session.commit()
    await message.answer(f"✅ <b>{data['anime_name']}</b> muvaffaqiyatli yangilandi!", parse_mode="HTML", reply_markup=get_admin_main_keyboard())


# ── ANIME O'CHIRISH ───────────────────────────────────────────────────────────

@router.message(F.text == "🗑 Anime o'chirish")
async def del_anime_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(DeleteAnimeState.waiting_for_anime_code)
    await message.answer("🗑 <b>Anime o'chirish</b>\n\n<b>Anime kodini kiriting:</b>", parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(DeleteAnimeState.waiting_for_anime_code)
async def del_anime_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Raqam kiriting!")
    code = int(message.text.strip())
    anime = await crud.get_anime_by_code(session, code)
    if not anime: return await message.answer(f"❌ {code} kodli anime topilmadi!")
    await state.update_data(anime_id=anime.id, anime_name=anime.name)
    await state.set_state(DeleteAnimeState.waiting_for_confirmation)
    await message.answer(
        f"⚠️ <b>{anime.name}</b> (kod: {code}) va uning barcha qismlari o'chirilsinmi?",
        parse_mode="HTML", reply_markup=get_confirmation_keyboard()
    )


@router.message(DeleteAnimeState.waiting_for_confirmation)
async def del_anime_confirm(message: Message, session, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    if message.text.strip() != "✅ Ha, tasdiqlash":
        return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    deleted = await crud.delete_anime(session, data["anime_id"])
    await session.commit()
    if deleted:
        await message.answer(f"✅ <b>{data['anime_name']}</b> o'chirildi!", parse_mode="HTML", reply_markup=get_admin_main_keyboard())
    else:
        await message.answer("❌ O'chirishda xato!", reply_markup=get_admin_main_keyboard())


# ── POSTER ALMASHTIRISH ───────────────────────────────────────────────────────

@router.message(F.text == "🖼 Poster almashtirish")
async def change_poster_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ChangePosterState.waiting_for_anime_code)
    await message.answer("🖼 <b>Poster almashtirish</b>\n\n<b>Anime kodini kiriting:</b>", parse_mode="HTML", reply_markup=get_cancel_keyboard())


@router.message(ChangePosterState.waiting_for_anime_code)
async def change_poster_code(message: Message, session, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    if not message.text.strip().isdigit(): return await message.answer("❌ Raqam kiriting!")
    code = int(message.text.strip())
    anime = await crud.get_anime_by_code(session, code)
    if not anime: return await message.answer(f"❌ {code} kodli anime topilmadi!")
    await state.update_data(anime_id=anime.id)
    await state.set_state(ChangePosterState.waiting_for_poster)
    await message.answer(f"✅ Anime: <b>{anime.name}</b>\n\n🖼 <b>Yangi posteri yuboring:</b>", parse_mode="HTML")


@router.message(ChangePosterState.waiting_for_poster, F.photo)
async def change_poster_save(message: Message, session, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    file_id = message.photo[-1].file_id
    await crud.update_anime_poster(session, data["anime_id"], file_id)
    await session.commit()
    await message.answer("✅ Poster muvaffaqiyatli almashtirildi!", reply_markup=get_admin_main_keyboard())


# ── BROADCAST ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Reklama yuborish")
async def broadcast_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Broadcast xabarini kiriting:</b>\n\n"
        "Matn, rasm, video yoki hujjat yuborishingiz mumkin.",
        parse_mode="HTML", reply_markup=get_cancel_keyboard()
    )


@router.message(BroadcastState.waiting_for_message)
async def broadcast_preview(message: Message, state: FSMContext) -> None:
    if _is_cancel(message.text): await state.clear(); return await message.answer("❌ Bekor.", reply_markup=get_admin_main_keyboard())
    media_file_id = None
    media_type = None
    msg_text = None

    if message.photo:
        media_file_id = message.photo[-1].file_id; media_type = "photo"; msg_text = message.caption
    elif message.video:
        media_file_id = message.video.file_id; media_type = "video"; msg_text = message.caption
    elif message.document:
        media_file_id = message.document.file_id; media_type = "document"; msg_text = message.caption
    else:
        msg_text = message.text

    await state.update_data(media_file_id=media_file_id, media_type=media_type, msg_text=msg_text)
    await state.set_state(BroadcastState.waiting_for_confirmation)
    preview_text = f"📢 <b>Broadcast ko'rinishi:</b>\n\n{msg_text or '(Media fayl)'}\n\n⚠️ Yuborilsinmi?"
    await message.answer(preview_text, parse_mode="HTML", reply_markup=get_broadcast_confirm_keyboard())


@router.callback_query(BroadcastState.waiting_for_confirmation, F.data.startswith("broadcast:"))
async def broadcast_execute(callback: CallbackQuery, session, state: FSMContext) -> None:
    action = callback.data.split(":")[1]
    if action == "cancel":
        await state.clear()
        await callback.message.answer("❌ Broadcast bekor qilindi.", reply_markup=get_admin_main_keyboard())
        await callback.answer()
        return
    data = await state.get_data()
    await state.clear()
    await callback.message.answer("📤 Xabar yuborilmoqda...", reply_markup=get_admin_main_keyboard())
    await callback.answer()
    user_ids = await crud.get_all_user_ids(session)
    sent = 0; failed = 0
    for uid in user_ids:
        try:
            if data.get("media_type") == "photo":
                await callback.bot.send_photo(uid, data["media_file_id"], caption=data.get("msg_text"), parse_mode="HTML")
            elif data.get("media_type") == "video":
                await callback.bot.send_video(uid, data["media_file_id"], caption=data.get("msg_text"), parse_mode="HTML")
            elif data.get("media_type") == "document":
                await callback.bot.send_document(uid, data["media_file_id"], caption=data.get("msg_text"), parse_mode="HTML")
            else:
                await callback.bot.send_message(uid, data["msg_text"], parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await callback.message.answer(
        f"✅ <b>Broadcast tugadi!</b>\n\n📤 Yuborildi: <b>{sent}</b>\n❌ Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ── BACKUP ────────────────────────────────────────────────────────────────────

@router.message(F.text == "💾 Backup yaratish")
async def make_backup(message: Message) -> None:
    await message.answer("⏳ Backup yaratilmoqda...")
    backup_path = await create_backup()
    if backup_path:
        backups = get_backup_list()
        backup_list_text = "\n".join(f"• {b['name']} ({b['size']}) — {b['created']}" for b in backups[:5])
        await message.answer(
            f"✅ <b>Backup yaratildi!</b>\n\n📁 Fayl: <code>{backup_path}</code>\n\n<b>So'nggi backuplar:</b>\n{backup_list_text}",
            parse_mode="HTML", reply_markup=get_admin_main_keyboard()
        )
    else:
        await message.answer("❌ Backup yaratishda xato!", reply_markup=get_admin_main_keyboard())


# ── ADMIN PANEL CALLBACK ──────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:panel")
async def admin_panel_callback(callback: CallbackQuery, session, state: FSMContext) -> None:
    await state.clear()
    stats = await crud.get_full_stats(session)
    from bot.config import ADMIN_PANEL_MESSAGE
    text = ADMIN_PANEL_MESSAGE.format(
        name=callback.from_user.full_name, user_id=callback.from_user.id,
        users=stats["users_count"], animes=stats["animes_count"],
        videos=stats["videos_count"], searches=stats["searches_count"],
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(callback: CallbackQuery, session) -> None:
    stats = await crud.get_full_stats(session)
    await callback.message.answer(format_stats(stats), parse_mode="HTML", reply_markup=get_back_to_admin_keyboard())
    await callback.answer()
