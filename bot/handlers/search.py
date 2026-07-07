"""
handlers/search.py - Qidiruv handlerlari
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database import crud
from bot.keyboards.inline import get_search_result_keyboard
from bot.keyboards.reply import get_main_keyboard

router = Router(name="search")


@router.message(F.text & ~F.text.startswith("/"))
async def global_text_search(message: Message, session, db_user, state: FSMContext) -> None:
    """Matn yozilganda anime nomini qidirish (agar hech qaysi holatda bo'lmasa)"""
    current_state = await state.get_state()
    if current_state is not None:
        return

    text = message.text.strip()

    # Raqam bo'lsa kod qidiruvi (user.py da ham bor, lekin FSM holatsiz)
    if text.isdigit():
        return

    # Tugma matnlari
    skip_texts = {
        "🆔 Kod orqali qidiruv", "🎬 Anime", "🖼 Rasm orqali qidiruv",
        "📚 Qo'llanma", "📋 Ro'yxat", "📢 Reklama",
        "➕ Anime qo'shish", "✏️ Anime tahrirlash", "🗑 Anime o'chirish",
        "🖼 Poster almashtirish", "🎬 Qism qo'shish", "❌ Qism o'chirish",
        "📊 Statistika", "👤 Foydalanuvchilar", "📢 Reklama yuborish",
        "⚙️ Sozlamalar", "💾 Backup yaratish", "🔙 Asosiy menyu",
        "❌ Bekor qilish", "✅ Ha, tasdiqlash", "❌ Yo'q, bekor",
        "⏭ O'tkazib yuborish", "➕ Yana qism qo'shish", "✅ Tugatish",
    }
    if text in skip_texts:
        return

    if len(text) < 2:
        return

    # Nom bo'yicha qidirish
    animes = await crud.search_anime_by_name(session, text)

    if not animes:
        await message.answer(
            f"🔍 <b>«{text}»</b> bo'yicha hech narsa topilmadi.\n\n"
            f"💡 Anime kodini kiriting yoki <b>📋 Ro'yxat</b> dan tanlang.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(),
        )
        return

    if len(animes) == 1:
        # Bitta topilsa to'g'ridan to'g'ri ko'rsat
        from bot.utils import format_anime_info
        from bot.keyboards.inline import get_anime_detail_keyboard
        anime = animes[0]
        is_fav = False
        if db_user:
            is_fav = await crud.is_favorite(session, db_user.id, anime.id)
        await crud.increment_anime_searches(session, anime.id)
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
                return
            except Exception:
                pass
        await message.answer(caption, parse_mode="HTML", reply_markup=keyboard)
        return

    # Ko'p natija — ro'yxat ko'rsat
    await message.answer(
        f"🔍 <b>«{text}»</b> bo'yicha <b>{len(animes)}</b> ta natija topildi:",
        parse_mode="HTML",
        reply_markup=get_search_result_keyboard(animes),
    )
