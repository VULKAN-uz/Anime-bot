"""
handlers/admin_handler.py - Admin panel handlerlari
=====================================================
Admin uchun barcha funksiyalar:
1. Admin panel bosh menyusi (/admin)
2. Anime qo'shish (to'liq flow)
3. Qism yuklash (video → file_id saqlash)
4. Anime tahrirlash
5. Anime o'chirish
6. Animeler ro'yxati
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.keyboards.admin_keyboards import (
    admin_main_keyboard,
    cancel_keyboard,
    confirm_keyboard,
    edit_fields_keyboard
)
from bot.states.admin_states import (
    AddAnimeStates,
    AddEpisodeStates,
    EditAnimeStates,
    DeleteAnimeStates
)
from bot.utils.helpers import is_admin, format_anime_list, validate_positive_int

logger = logging.getLogger(__name__)

# Router yaratish (faqat admin uchun)
router = Router()


# ==========================================
# Admin tekshirish filteri
# ==========================================
def admin_filter(message: Message) -> bool:
    """Faqat adminlar uchun ruxsat beradi."""
    return is_admin(message.from_user.id)


# ==========================================
# /admin - Bosh menyu
# ==========================================
@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Admin paneliga kirish."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q!")
        return

    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


# ==========================================
# 📋 Animlar ro'yxati
# ==========================================
@router.message(F.text == "📋 Animlar ro'yxati", admin_filter)
async def list_animes(message: Message) -> None:
    """Barcha animelарни ro'yxatini chiqaradi."""
    animes = await db.get_all_animes()
    text = format_anime_list(animes)
    await message.answer(text, parse_mode="HTML")


# ==========================================
# ➕ ANIME QO'SHISH - 1: Kod
# ==========================================
@router.message(F.text == "➕ Anime qo'shish", admin_filter)
async def add_anime_start(message: Message, state: FSMContext) -> None:
    """Anime qo'shish jarayonini boshlaydi."""
    await state.set_state(AddAnimeStates.waiting_code)
    await message.answer(
        "➕ <b>Yangi anime qo'shish</b>\n\n"
        "1️⃣ Anime kodini kiriting (raqam):\n"
        "<i>Masalan: 1, 2, 3...</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddAnimeStates.waiting_code, admin_filter)
async def add_anime_code(message: Message, state: FSMContext) -> None:
    """Anime kodini qabul qiladi."""
    # Bekor qilish
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    code = validate_positive_int(message.text)
    if code is None:
        await message.answer("⚠️ Iltimos, musbat raqam kiriting!")
        return

    # Kod mavjudligini tekshirish
    if await db.check_code_exists(code):
        await message.answer(f"⚠️ <b>{code}</b> kodi allaqachon mavjud! Boshqa kod kiriting.", parse_mode="HTML")
        return

    await state.update_data(code=code)
    await state.set_state(AddAnimeStates.waiting_name)
    await message.answer(
        f"✅ Kod: <b>{code}</b>\n\n"
        "2️⃣ Anime nomini kiriting:",
        parse_mode="HTML"
    )


# ==========================================
# ➕ ANIME QO'SHISH - 2: Nom
# ==========================================
@router.message(AddAnimeStates.waiting_name, admin_filter)
async def add_anime_name(message: Message, state: FSMContext) -> None:
    """Anime nomini qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Nom juda qisqa! Kamida 2 ta harf kiriting.")
        return

    await state.update_data(name=name)
    await state.set_state(AddAnimeStates.waiting_poster)
    await message.answer(
        f"✅ Nom: <b>{name}</b>\n\n"
        "3️⃣ Poster rasmini yuboring (foto):\n"
        "<i>Yoki /skip deb yozing (o'tkazib yuborish)</i>",
        parse_mode="HTML"
    )


# ==========================================
# ➕ ANIME QO'SHISH - 3: Poster
# ==========================================
@router.message(AddAnimeStates.waiting_poster, F.photo, admin_filter)
async def add_anime_poster_photo(message: Message, state: FSMContext) -> None:
    """Poster rasmini qabul qiladi va file_id ni saqlaydi."""
    # Eng katta o'lchamdagi rasmni olish
    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(poster=file_id)
    await state.set_state(AddAnimeStates.waiting_genre)
    await message.answer(
        "✅ Poster saqlandi!\n\n"
        "4️⃣ Janrini kiriting:\n"
        "<i>Masalan: Aksion, Romantik, Fantastika...</i>",
        parse_mode="HTML"
    )


@router.message(AddAnimeStates.waiting_poster, Command("skip"), admin_filter)
@router.message(AddAnimeStates.waiting_poster, F.text == "/skip", admin_filter)
async def add_anime_poster_skip(message: Message, state: FSMContext) -> None:
    """Posterni o'tkazib yuboradi."""
    await state.update_data(poster="")
    await state.set_state(AddAnimeStates.waiting_genre)
    await message.answer(
        "⏭ Poster o'tkazib yuborildi.\n\n"
        "4️⃣ Janrini kiriting:\n"
        "<i>Masalan: Aksion, Romantik, Fantastika...</i>",
        parse_mode="HTML"
    )


@router.message(AddAnimeStates.waiting_poster, admin_filter)
async def add_anime_poster_invalid(message: Message) -> None:
    """Noto'g'ri poster yuborilganda."""
    if message.text == "❌ Bekor qilish":
        return  # Yuqoridagi handler ushlaydi
    await message.answer("⚠️ Iltimos, rasm yuboring yoki /skip deb yozing!")


# ==========================================
# ➕ ANIME QO'SHISH - 4: Janr
# ==========================================
@router.message(AddAnimeStates.waiting_genre, admin_filter)
async def add_anime_genre(message: Message, state: FSMContext) -> None:
    """Janrni qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    genre = message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddAnimeStates.waiting_language)
    await message.answer(
        f"✅ Janr: <b>{genre}</b>\n\n"
        "5️⃣ Tilini kiriting:\n"
        "<i>Masalan: O'zbek, Rus, Yapon (O'zbek subtitri)...</i>",
        parse_mode="HTML"
    )


# ==========================================
# ➕ ANIME QO'SHISH - 5: Til
# ==========================================
@router.message(AddAnimeStates.waiting_language, admin_filter)
async def add_anime_language(message: Message, state: FSMContext) -> None:
    """Tilni qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    language = message.text.strip()
    await state.update_data(language=language)
    await state.set_state(AddAnimeStates.waiting_description)
    await message.answer(
        f"✅ Til: <b>{language}</b>\n\n"
        "6️⃣ Tavsifini kiriting:",
        parse_mode="HTML"
    )


# ==========================================
# ➕ ANIME QO'SHISH - 6: Tavsif
# ==========================================
@router.message(AddAnimeStates.waiting_description, admin_filter)
async def add_anime_description(message: Message, state: FSMContext) -> None:
    """Tavsifni qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddAnimeStates.waiting_episodes)
    await message.answer(
        "7️⃣ Umumiy qismlar sonini kiriting (raqam):\n"
        "<i>Masalan: 12, 24, 26...</i>",
        parse_mode="HTML"
    )


# ==========================================
# ➕ ANIME QO'SHISH - 7: Qismlar soni → Saqlash
# ==========================================
@router.message(AddAnimeStates.waiting_episodes, admin_filter)
async def add_anime_episodes(message: Message, state: FSMContext) -> None:
    """Qismlar sonini qabul qilib, animeni bazaga saqlaydi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    episodes = validate_positive_int(message.text)
    if episodes is None:
        await message.answer("⚠️ Iltimos, musbat raqam kiriting!")
        return

    # Barcha ma'lumotlarni olish
    data = await state.get_data()
    await state.clear()

    # Bazaga saqlash
    anime_id = await db.add_anime(
        code=data["code"],
        name=data["name"],
        poster=data.get("poster", ""),
        genre=data["genre"],
        language=data["language"],
        description=data["description"],
        episodes=episodes
    )

    if anime_id:
        await message.answer(
            f"✅ <b>Anime muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🔢 Kod: <b>{data['code']}</b>\n"
            f"📝 Nom: <b>{data['name']}</b>\n"
            f"📺 Qismlar: <b>{episodes}</b>\n\n"
            f"🎬 Endi qismlarni yuklash uchun <b>«🎬 Qism yuklash»</b> tugmasini bosing.",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Xatolik! Anime saqlashda muammo yuz berdi.",
            reply_markup=admin_main_keyboard()
        )


# ==========================================
# 🎬 QISM YUKLASH - 1: Anime kodi
# ==========================================
@router.message(F.text == "🎬 Qism yuklash", admin_filter)
async def add_episode_start(message: Message, state: FSMContext) -> None:
    """Qism yuklash jarayonini boshlaydi."""
    await state.set_state(AddEpisodeStates.waiting_anime_code)
    await message.answer(
        "🎬 <b>Qism yuklash</b>\n\n"
        "1️⃣ Animeni kodini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddEpisodeStates.waiting_anime_code, admin_filter)
async def add_episode_code(message: Message, state: FSMContext) -> None:
    """Anime kodini qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    code = validate_positive_int(message.text)
    if code is None:
        await message.answer("⚠️ Iltimos, raqam kiriting!")
        return

    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>{code}</b> kodli anime topilmadi!", parse_mode="HTML")
        return

    await state.update_data(anime_id=anime["id"], anime_name=anime["name"], total_eps=anime["episodes"])
    await state.set_state(AddEpisodeStates.waiting_episode_num)
    await message.answer(
        f"✅ Anime: <b>{anime['name']}</b>\n"
        f"📺 Jami qismlar: <b>{anime['episodes']}</b>\n\n"
        f"2️⃣ Qism raqamini kiriting (1 dan {anime['episodes']} gacha):",
        parse_mode="HTML"
    )


# ==========================================
# 🎬 QISM YUKLASH - 2: Qism raqami
# ==========================================
@router.message(AddEpisodeStates.waiting_episode_num, admin_filter)
async def add_episode_num(message: Message, state: FSMContext) -> None:
    """Qism raqamini qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    ep_num = validate_positive_int(message.text)
    data = await state.get_data()
    total = data.get("total_eps", 9999)

    if ep_num is None or ep_num > total:
        await message.answer(f"⚠️ Iltimos, 1 dan {total} gacha raqam kiriting!")
        return

    await state.update_data(episode_num=ep_num)
    await state.set_state(AddEpisodeStates.waiting_video)
    await message.answer(
        f"3️⃣ <b>{ep_num}-qism</b> videosini yuboring:\n\n"
        "⚠️ Video <b>fayl sifatida</b> yuboring (Document), "
        "shunda sifat yo'qolmaydi.",
        parse_mode="HTML"
    )


# ==========================================
# 🎬 QISM YUKLASH - 3: Video → file_id saqlash
# ==========================================
@router.message(AddEpisodeStates.waiting_video, F.video, admin_filter)
async def add_episode_video(message: Message, state: FSMContext) -> None:
    """Video (video sifatida) file_id sini saqlaydi."""
    file_id = message.video.file_id
    data = await state.get_data()
    await state.clear()

    success = await db.add_episode(
        anime_id=data["anime_id"],
        episode_num=data["episode_num"],
        file_id=file_id
    )

    if success:
        await message.answer(
            f"✅ <b>{data['episode_num']}-qism</b> muvaffaqiyatli saqlandi!\n"
            f"📝 Anime: <b>{data['anime_name']}</b>\n"
            f"🆔 file_id: <code>{file_id[:30]}...</code>",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Saqlashda xato!", reply_markup=admin_main_keyboard())


@router.message(AddEpisodeStates.waiting_video, F.document, admin_filter)
async def add_episode_document(message: Message, state: FSMContext) -> None:
    """Video (dokument sifatida) file_id sini saqlaydi."""
    file_id = message.document.file_id
    data = await state.get_data()
    await state.clear()

    success = await db.add_episode(
        anime_id=data["anime_id"],
        episode_num=data["episode_num"],
        file_id=file_id
    )

    if success:
        await message.answer(
            f"✅ <b>{data['episode_num']}-qism</b> muvaffaqiyatli saqlandi!\n"
            f"📝 Anime: <b>{data['anime_name']}</b>\n"
            f"🆔 file_id: <code>{file_id[:30]}...</code>",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )


@router.message(AddEpisodeStates.waiting_video, admin_filter)
async def add_episode_invalid(message: Message) -> None:
    """Noto'g'ri fayl yuborilganda."""
    if message.text == "❌ Bekor qilish":
        return
    await message.answer("⚠️ Iltimos, video yuboring!")


# ==========================================
# ✏️ TAHRIRLASH - 1: Anime kodi
# ==========================================
@router.message(F.text == "✏️ Tahrirlash", admin_filter)
async def edit_anime_start(message: Message, state: FSMContext) -> None:
    """Tahrirlash jarayonini boshlaydi."""
    await state.set_state(EditAnimeStates.waiting_anime_code)
    await message.answer(
        "✏️ <b>Anime tahrirlash</b>\n\n"
        "Tahrirlash kerak bo'lgan anime kodini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(EditAnimeStates.waiting_anime_code, admin_filter)
async def edit_anime_code(message: Message, state: FSMContext) -> None:
    """Tahrirlash uchun anime kodini qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    code = validate_positive_int(message.text)
    if code is None:
        await message.answer("⚠️ Iltimos, raqam kiriting!")
        return

    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>{code}</b> kodli anime topilmadi!", parse_mode="HTML")
        return

    await state.update_data(anime_id=anime["id"], anime_name=anime["name"])
    await state.set_state(EditAnimeStates.waiting_field)
    await message.answer(
        f"✏️ <b>{anime['name']}</b> — qaysi maydonni o'zgartirmoqchisiz?",
        reply_markup=edit_fields_keyboard(),
        parse_mode="HTML"
    )


# ==========================================
# ✏️ TAHRIRLASH - 2: Maydon tanlash (inline callback)
# ==========================================
@router.callback_query(F.data.startswith("edit_field:"))
async def edit_field_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """Tahrirlash uchun maydon tanlanadi."""
    current_state = await state.get_state()
    if current_state != EditAnimeStates.waiting_field:
        await callback.answer("⚠️ Iltimos, avval anime kodini kiriting!")
        return

    field = callback.data.split(":")[1]
    field_names = {
        "name": "Nomi",
        "poster": "Posteri (rasm yuboring)",
        "genre": "Janri",
        "language": "Tili",
        "description": "Tavsifi",
        "episodes": "Qismlar soni",
        "code": "Kodi"
    }

    await state.update_data(edit_field=field)
    await state.set_state(EditAnimeStates.waiting_new_value)
    await callback.message.edit_text(
        f"✏️ <b>{field_names.get(field, field)}</b> uchun yangi qiymat kiriting:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_cancel")
async def edit_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Tahrirlashni bekor qiladi."""
    await state.clear()
    await callback.message.edit_text("❌ Tahrirlash bekor qilindi.")
    await callback.answer()


# ==========================================
# ✏️ TAHRIRLASH - 3: Yangi qiymat
# ==========================================
@router.message(EditAnimeStates.waiting_new_value, admin_filter)
async def edit_anime_value(message: Message, state: FSMContext) -> None:
    """Yangi qiymatni qabul qilib, bazani yangilaydi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    data = await state.get_data()
    field = data.get("edit_field")
    anime_id = data.get("anime_id")

    # Poster uchun rasm
    if field == "poster":
        if message.photo:
            new_value = message.photo[-1].file_id
        else:
            await message.answer("⚠️ Iltimos, rasm yuboring!")
            return
    elif field in ("episodes", "code"):
        # Raqamli maydonlar
        num = validate_positive_int(message.text)
        if num is None:
            await message.answer("⚠️ Iltimos, musbat raqam kiriting!")
            return
        # Kod uchun unikal tekshirish
        if field == "code" and await db.check_code_exists(num, exclude_id=anime_id):
            await message.answer(f"⚠️ <b>{num}</b> kodi allaqachon mavjud!", parse_mode="HTML")
            return
        new_value = str(num)
    else:
        new_value = message.text.strip()

    await state.clear()

    success = await db.update_anime(anime_id, field, new_value)
    if success:
        await message.answer(
            f"✅ <b>{data['anime_name']}</b> ma'lumotlari yangilandi!",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Yangilashda xato!", reply_markup=admin_main_keyboard())


# ==========================================
# 🗑 O'CHIRISH - 1: Anime kodi
# ==========================================
@router.message(F.text == "🗑 O'chirish", admin_filter)
async def delete_anime_start(message: Message, state: FSMContext) -> None:
    """O'chirish jarayonini boshlaydi."""
    await state.set_state(DeleteAnimeStates.waiting_anime_code)
    await message.answer(
        "🗑 <b>Anime o'chirish</b>\n\n"
        "O'chirish kerak bo'lgan anime kodini kiriting:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(DeleteAnimeStates.waiting_anime_code, admin_filter)
async def delete_anime_code(message: Message, state: FSMContext) -> None:
    """O'chirish uchun anime kodini qabul qiladi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    code = validate_positive_int(message.text)
    if code is None:
        await message.answer("⚠️ Iltimos, raqam kiriting!")
        return

    anime = await db.get_anime_by_code(code)
    if not anime:
        await message.answer(f"❌ <b>{code}</b> kodli anime topilmadi!", parse_mode="HTML")
        return

    await state.update_data(anime_id=anime["id"], anime_name=anime["name"])
    await state.set_state(DeleteAnimeStates.waiting_confirm)
    await message.answer(
        f"⚠️ <b>Diqqat!</b>\n\n"
        f"🗑 <b>{anime['name']}</b> animesini o'chirmoqchimisiz?\n"
        f"(Barcha qismlar ham o'chib ketadi!)",
        reply_markup=confirm_keyboard(),
        parse_mode="HTML"
    )


# ==========================================
# 🗑 O'CHIRISH - 2: Tasdiqlash
# ==========================================
@router.message(DeleteAnimeStates.waiting_confirm, admin_filter)
async def delete_anime_confirm(message: Message, state: FSMContext) -> None:
    """O'chirishni tasdiqlaydi yoki bekor qiladi."""
    data = await state.get_data()
    await state.clear()

    if message.text == "✅ Ha, o'chirish":
        success = await db.delete_anime(data["anime_id"])
        if success:
            await message.answer(
                f"✅ <b>{data['anime_name']}</b> muvaffaqiyatli o'chirildi!",
                reply_markup=admin_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ O'chirishda xato!", reply_markup=admin_main_keyboard())
    else:
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
