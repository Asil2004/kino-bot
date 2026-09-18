from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

import config
from database import (
    add_movie, get_movie, delete_movie, count_movies, count_users, get_all_users,
    get_recent_movies, add_episode, get_episodes, delete_episode,
    add_channel, get_channels, delete_channel
)
from keyboards import get_admin_main_kb, get_cancel_kb

admin_router = Router()


# FSM holatlari
class AddSingleMovieState(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_genre = State()


class AddSeriesState(StatesGroup):
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_year = State()
    waiting_for_genre = State()
    waiting_for_photo = State()


class AddEpisodeState(StatesGroup):
    waiting_for_code = State()
    waiting_for_number = State()
    waiting_for_video = State()


class DeleteMovieState(StatesGroup):
    waiting_for_code = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


class AddChannelState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_link = State()


class EditInstagramState(StatesGroup):
    waiting_for_insta = State()


class DeleteChannelState(StatesGroup):
    waiting_for_id = State()


def is_admin(user_id: int) -> bool:
    return not config.ADMINS or user_id in config.ADMINS


# ==================== ASOSIY ADMIN BUYRUQLARI ====================

@admin_router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "👑 <b>Admin boshqaruv paneliga xush kelibsiz!</b>\n\n"
        "Quyidagi tugmalardan kerakli bo'limni tanlang:",
        reply_markup=get_admin_main_kb(),
        parse_mode="HTML"
    )


@admin_router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await message.answer("✅ Amal bekor qilindi.", reply_markup=get_admin_main_kb())


from aiogram.fsm.state import default_state


# Admin to'g'ridan-to'g'ri video yoki fayl yuborganida (istalgan payt)
@admin_router.message(default_state, F.video | F.document | F.animation | F.audio)
async def direct_media_upload_handler(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    caption = message.caption or ""

    # Agar izohida /add 105 Forsaj 10 bo'lsa
    if caption.startswith("/add "):
        parts = caption.split(maxsplit=2)
        if len(parts) >= 3:
            code = parts[1].strip()
            title = parts[2].strip()
            file_id = message.video.file_id if message.video else message.document.file_id
            bot_info = await bot.get_me()
            c_text = f"🎬 <b>{title}</b>\n\n🔢 Kino kodi: <code>{code}</code>\n\n🤖 Bot: @{bot_info.username}"
            success = await add_movie(code=code, file_id=file_id, title=title, movie_type="single", caption=c_text)
            if success:
                await message.answer(
                    f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n🎬 Nomi: <b>{title}</b>\n🔢 Kodi: <code>{code}</code>\n🔗 Havola: https://t.me/{bot_info.username}?start={code}",
                    reply_markup=get_admin_main_kb(),
                    parse_mode="HTML"
                )
                return

    # Agar izohida /addpart 205 1 bo'lsa
    if caption.startswith("/addpart "):
        parts = caption.split()
        if len(parts) >= 3 and parts[2].isdigit():
            code = parts[1].strip()
            ep_num = int(parts[2])
            file_id = message.video.file_id if message.video else message.document.file_id
            success = await add_episode(movie_code=code, episode_number=ep_num, file_id=file_id)
            if success:
                await message.answer(f"✅ <code>{code}</code> serialiga <b>{ep_num}-qism</b> muvaffaqiyatli qo'shildi!", reply_markup=get_admin_main_kb(), parse_mode="HTML")
                return

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.audio:
        file_id = message.audio.file_id

    await state.update_data(file_id=file_id, caption=caption)
    await state.set_state(AddSingleMovieState.waiting_for_code)

    await message.answer(
        "📹 <b>Video / Fayl qabul qilindi!</b>\n\n"
        "🔢 Ushbu kino uchun <b>noyob kod</b> kiriting (Masalan: <code>101</code>):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


# ==================== BITTA FILM QO'SHISH ====================

@admin_router.message(F.text == "🎬 Bitta Film qo'shish")
async def start_add_single(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddSingleMovieState.waiting_for_video)
    await message.answer(
        "📹 Iltimos, kino <b>videosini</b> yoki <b>faylini</b> yuboring:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddSingleMovieState.waiting_for_video, F.video | F.document | F.animation | F.audio)
async def process_single_video(message: Message, state: FSMContext):
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.audio:
        file_id = message.audio.file_id

    caption = message.caption or ""

    await state.update_data(file_id=file_id, caption=caption)
    await state.set_state(AddSingleMovieState.waiting_for_code)

    await message.answer(
        "🔢 Ushbu kino uchun <b>noyob kod</b> kiriting (Masalan: <code>101</code>):",
        parse_mode="HTML"
    )


@admin_router.message(AddSingleMovieState.waiting_for_code, F.text)
async def process_single_code(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AddSingleMovieState.waiting_for_title)

    await message.answer(
        "📝 Kino nomini kiriting (Masalan: <i>Forsaj 10 (2023)</i>):",
        parse_mode="HTML"
    )


@admin_router.message(AddSingleMovieState.waiting_for_title, F.text)
async def process_single_title(message: Message, state: FSMContext, bot: Bot):
    title = message.text.strip()
    data = await state.get_data()
    file_id = data["file_id"]
    code = data["code"]
    caption = data.get("caption", "")

    if not caption:
        bot_info = await bot.get_me()
        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"🔢 Kino kodi: <code>{code}</code>\n"
            f"🤖 Bot: @{bot_info.username}"
        )

    success = await add_movie(
        code=code, file_id=file_id, title=title, 
        movie_type="single", caption=caption
    )
    await state.clear()

    if success:
        bot_info = await bot.get_me()
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 Nomi: <b>{title}</b>\n"
            f"🔢 Kodi: <code>{code}</code>\n"
            f"🔗 Havola: https://t.me/{bot_info.username}?start={code}",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ <b>Xatolik:</b> <code>{code}</code> kodli kino allaqachon mavjud!",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )


# ==================== SERIAL YARATISH ====================

@admin_router.message(F.text == "📺 Serial yaratish")
async def start_add_series(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddSeriesState.waiting_for_code)
    await message.answer(
        "📺 <b>Yangi Serial yaratish:</b>\n\n"
        "🔢 Serial uchun <b>noyob kod</b> kiriting (Masalan: <code>205</code> yoki <code>qashqirlar</code>):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddSeriesState.waiting_for_code, F.text)
async def process_series_code(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AddSeriesState.waiting_for_title)
    await message.answer("📝 Serial nomini kiriting (Masalan: <i>Qashqirlar Makoni</i>):", parse_mode="HTML")


@admin_router.message(AddSeriesState.waiting_for_title, F.text)
async def process_series_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(AddSeriesState.waiting_for_year)
    await message.answer("📅 Chiqarilgan yili (Masalan: <code>2007</code> yoki /otkaz):", parse_mode="HTML")


@admin_router.message(AddSeriesState.waiting_for_year, F.text)
async def process_series_year(message: Message, state: FSMContext):
    year = "" if message.text.strip() in ["/otkaz", "/skip"] else message.text.strip()
    await state.update_data(year=year)
    await state.set_state(AddSeriesState.waiting_for_genre)
    await message.answer("🎭 Janri (Masalan: <i>Sarguzasht, Fantastika</i> yoki /otkaz):", parse_mode="HTML")


@admin_router.message(AddSeriesState.waiting_for_genre, F.text)
async def process_series_genre(message: Message, state: FSMContext):
    genre = "" if message.text.strip() in ["/otkaz", "/skip"] else message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddSeriesState.waiting_for_photo)
    await message.answer(
        "🖼 Serial uchun <b>Poster rasmini</b> yuboring (yoki rasmsiz qoldirish uchun /otkaz deb yozing):",
        parse_mode="HTML"
    )


@admin_router.message(AddSeriesState.waiting_for_photo, F.photo | (F.text.in_(["/otkaz", "/skip"])))
async def process_series_finish(message: Message, state: FSMContext, bot: Bot):
    photo_id = message.photo[-1].file_id if message.photo else ""
    data = await state.get_data()
    code = data["code"]
    title = data["title"]
    year = data.get("year", "")
    genre = data.get("genre", "")

    bot_info = await bot.get_me()
    caption = (
        f"📺 <b>{title}</b>\n\n"
        f"🔢 Serial kodi: <code>{code}</code>\n"
        f"📅 Yili: {year or 'Ko''rsatilmagan'}\n"
        f"🎭 Janri: {genre or 'Ko''rsatilmagan'}\n"
        f"🇺🇿 Tili: O'zbek tilida\n\n"
        f"🤖 Bot: @{bot_info.username}"
    )

    success = await add_movie(
        code=code, file_id="", title=title, movie_type="series",
        year=year, genre=genre, photo_id=photo_id, caption=caption
    )
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>«{title}» seriali muvaffaqiyatli yaratildi!</b>\n\n"
            f"🔢 Kodi: <code>{code}</code>\n"
            f"Endi <b>«➕ Serialga qism qo'shish»</b> tugmasi orqali unga qismlarni (1-qism, 2-qism...) yuklashingiz mumkin.",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(f"❌ <code>{code}</code> kodli serial allaqachon mavjud!", reply_markup=get_admin_main_kb())


# ==================== SERIALGA QISM QO'SHISH ====================

@admin_router.message(F.text == "➕ Serialga qism qo'shish")
async def start_add_episode(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddEpisodeState.waiting_for_code)
    await message.answer(
        "➕ <b>Serialga qism qo'shish:</b>\n\n"
        "Qaysi serialga qism qo'shmoqchisiz? Serial <b>kodini</b> kiriting (Masalan: <code>205</code>):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeState.waiting_for_code, F.text)
async def process_episode_code(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await get_movie(code)
    if not movie:
        await message.answer(f"❌ <code>{code}</code> kodli serial topilmadi! Avval serialni yarating.", reply_markup=get_admin_main_kb(), parse_mode="HTML")
        await state.clear()
        return

    episodes = await get_episodes(code)
    next_ep = len(episodes) + 1

    await state.update_data(movie_code=code, movie_title=movie["title"])
    await state.set_state(AddEpisodeState.waiting_for_number)
    await message.answer(
        f"🎬 Serial: <b>{movie['title']}</b>\n"
        f"Mavjud qismlar: {len(episodes)} ta\n\n"
        f"Qism raqamini kiriting (Tavsiya: <code>{next_ep}</code>):",
        parse_mode="HTML"
    )


@admin_router.message(AddEpisodeState.waiting_for_number, F.text)
async def process_episode_num(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (Masalan: 1, 2, 3):")
        return

    await state.update_data(episode_number=int(text))
    await state.set_state(AddEpisodeState.waiting_for_video)
    await message.answer(f"📹 <b>{text}-qism</b> videosini yoki faylini yuboring:", parse_mode="HTML")


@admin_router.message(AddEpisodeState.waiting_for_video, F.video | F.document | F.animation | F.audio)
async def process_episode_video(message: Message, state: FSMContext):
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.audio:
        file_id = message.audio.file_id

    data = await state.get_data()
    movie_code = data["movie_code"]
    movie_title = data["movie_title"]
    ep_num = data["episode_number"]

    success = await add_episode(movie_code=movie_code, episode_number=ep_num, file_id=file_id)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>{movie_title}</b> serialiga <b>{ep_num}-qism</b> muvaffaqiyatli qo'shildi!\n\n"
            f"Yana qism qo'shish uchun: «➕ Serialga qism qo'shish» tugmasini bosing.",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Qismni saqlashda xatolik yuz berdi!", reply_markup=get_admin_main_kb())


# Tezkor qism qo'shish: /addpart <serial_kodi> <qism_raqami>
@admin_router.message(Command("addpart"))
async def quick_add_part(message: Message):
    if not is_admin(message.from_user.id):
        return

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.reply_to_message:
        if message.reply_to_message.video:
            file_id = message.reply_to_message.video.file_id
        elif message.reply_to_message.document:
            file_id = message.reply_to_message.document.file_id

    parts = message.text.split() if message.text else []
    if len(parts) < 3 or not file_id:
        await message.answer(
            "ℹ️ <b>Tezkor qism qo'shish:</b>\n"
            "Videoni yuborayotganda izohiga yoki videoga javob (reply) tarzida yozing:\n"
            "<code>/addpart [serial_kodi] [qism_raqami]</code>\n"
            "Masalan: <code>/addpart 205 1</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    ep_num = int(parts[2].strip()) if parts[2].strip().isdigit() else None
    if ep_num is None:
        await message.answer("Qism raqami faqat son bo'lishi kerak!")
        return

    success = await add_episode(movie_code=code, episode_number=ep_num, file_id=file_id)
    if success:
        await message.answer(f"✅ <code>{code}</code> serialiga <b>{ep_num}-qism</b> qo'shildi!", parse_mode="HTML")
    else:
        await message.answer("❌ Qismni saqlashda xatolik yuz berdi!", parse_mode="HTML")


# Tezkor bitta kino qo'shish buyrug'i: /add <kod> <nomi>
@admin_router.message(Command("add"))
async def quick_add_movie(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.reply_to_message:
        if message.reply_to_message.video:
            file_id = message.reply_to_message.video.file_id
        elif message.reply_to_message.document:
            file_id = message.reply_to_message.document.file_id

    if not file_id:
        await message.answer(
            "ℹ️ <b>Tezkor kino qo'shish:</b>\n"
            "Videoni yuborayotganda izohiga yoki javob qilib <code>/add 105 Forsaj 10</code> deb yozing.",
            parse_mode="HTML"
        )
        return

    parts = message.text.split(maxsplit=2) if message.text else []
    if len(parts) < 3:
        await message.answer(
            "⚠️ Format: <code>/add [kod] [kino nomi]</code>\nMasalan: <code>/add 105 Forsaj 10</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    title = parts[2].strip()

    bot_info = await bot.get_me()
    caption = (
        f"🎬 <b>{title}</b>\n\n"
        f"🔢 Kino kodi: <code>{code}</code>\n"
        f"🤖 Bot: @{bot_info.username}"
    )

    success = await add_movie(code=code, file_id=file_id, title=title, movie_type="single", caption=caption)
    if success:
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 Nomi: <b>{title}</b>\n"
            f"🔢 Kodi: <code>{code}</code>\n"
            f"🔗 Havola: https://t.me/{bot_info.username}?start={code}",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"❌ <code>{code}</code> kodli kino allaqachon mavjud!", parse_mode="HTML")


# ==================== O'CHIRISH ====================

@admin_router.message(F.text == "🗑 O'chirish")
async def start_delete_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(DeleteMovieState.waiting_for_code)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan kino yoki serialingiz <b>kodini</b> kiriting:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(DeleteMovieState.waiting_for_code, F.text)
async def process_delete_movie(message: Message, state: FSMContext):
    code = message.text.strip()
    success = await delete_movie(code)
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{code}</code> kodli kino/serial va uning barcha qismlari bazadan o'chirildi.", reply_markup=get_admin_main_kb(), parse_mode="HTML")
    else:
        await message.answer(f"❌ <code>{code}</code> kodli kino topilmadi!", reply_markup=get_admin_main_kb(), parse_mode="HTML")


# ==================== STATISTIKA ====================

@admin_router.message(F.text == "📊 Statistika")
async def stats_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    users_count = await count_users()
    movies_count = await count_movies()

    await message.answer(
        f"📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users_count} ta</b>\n"
        f"🎬 Baza hajmi (Kino & Seriallar): <b>{movies_count} ta</b>",
        parse_mode="HTML"
    )


@admin_router.message(F.text == "📋 Barcha kinolar")
async def recent_movies_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    movies = await get_recent_movies(limit=25)
    if not movies:
        await message.answer("Bazaga hali kino yoki serial qo'shilmagan.")
        return

    text = "📋 <b>Bazadagi so'nggi kinolar va seriallar:</b>\n\n"
    for code, title, m_type, views in movies:
        icon = "📺 [Serial]" if m_type == "series" else "🎬 [Film]"
        text += f"{icon} <b>{title}</b> — Kod: <code>{code}</code> (👁 {views})\n"

    await message.answer(text, parse_mode="HTML")


# ==================== KANALLARNI BOSHQARISH ====================

@admin_router.message(F.text == "📢 Kanallarni boshqarish")
async def manage_channels_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    channels = await get_channels()
    from database import get_setting, set_setting
    insta_url = await get_setting("INSTAGRAM_URL", config.INSTAGRAM_URL)
    insta_name = await get_setting("INSTAGRAM_NAME", config.INSTAGRAM_NAME)

    text = "📢 <b>Majburiy obuna va Kanallar boshqaruvi:</b>\n\n"

    if insta_url:
        text += f"📸 <b>Ulangan Instagram:</b> @{insta_name}\n🔗 {insta_url}\n\n"
    else:
        text += "📸 <i>Instagram ulanmagan.</i>\n\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []

    if channels:
        text += "📢 <b>Ulangan Telegram kanallar:</b>\n"
        for ch in channels:
            text += f"🔹 <b>{ch[2]}</b> (<code>{ch[1]}</code>)\n🔗 {ch[3]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"🗑 {ch[2]} ni o'chirish", callback_data=f"del_channel:{ch[1]}")
            ])
    else:
        text += "📢 <i>Hozircha Telegram kanal ulanmagan.</i>\n\n"

    buttons.append([InlineKeyboardButton(text="➕ Yangi kanal/guruh qo'shish", callback_data="add_channel_btn")])
    buttons.append([InlineKeyboardButton(text="📸 Instagramni o'zgartirish", callback_data="edit_insta_btn")])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


@admin_router.callback_query(F.data == "edit_insta_btn")
async def edit_insta_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(EditInstagramState.waiting_for_insta)
    await callback.message.answer(
        "📸 <b>Instagram sahifasini o'zgartirish:</b>\n\n"
        "Yangi Instagram username (@username) yoki to'liq havolasini yuboring (Masalan: <code>asilbek_ravshanov04</code> yoki <code>https://instagram.com/asilbek_ravshanov04</code>):\n\n"
        "<i>Instagramni o'chirish uchun /ochirish deb yozing.</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(EditInstagramState.waiting_for_insta, F.text)
async def process_edit_insta(message: Message, state: FSMContext):
    from database import set_setting
    text = message.text.strip()
    await state.clear()

    if text in ["/ochirish", "/delete", "/none"]:
        await set_setting("INSTAGRAM_URL", "")
        await set_setting("INSTAGRAM_NAME", "")
        await message.answer("✅ Instagram sahifasi obunalar ro'yxatidan olib tashlandi.", reply_markup=get_admin_main_kb())
        return

    insta_name = text.replace("https://instagram.com/", "").replace("https://www.instagram.com/", "").replace("@", "").strip().strip("/")
    insta_url = f"https://instagram.com/{insta_name}"

    await set_setting("INSTAGRAM_URL", insta_url)
    await set_setting("INSTAGRAM_NAME", insta_name)

    await message.answer(
        f"✅ <b>Instagram sahifasi muvaffaqiyatli saqlandi!</b>\n\n"
        f"📸 Profil: <b>@{insta_name}</b>\n"
        f"🔗 Havola: {insta_url}",
        reply_markup=get_admin_main_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "add_channel_btn")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AddChannelState.waiting_for_id)
    await callback.message.answer(
        "📢 <b>Kanal yoki Guruhni ulash:</b>\n\n"
        "Kanal username (@kanal_nomi), havolasi (https://t.me/...) yoki ID raqamini kiriting:\n\n"
        "⚠️ <b>MUHIM:</b> Bot ushbu kanalda/guruhda <b>ADMIN</b> bo'lishi kerak!",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(AddChannelState.waiting_for_id, F.text)
async def add_channel_id(message: Message, state: FSMContext, bot: Bot):
    raw_input = message.text.strip()
    channel_id = raw_input
    suggested_link = raw_input
    suggested_name = "Kanal"

    if "t.me/" in raw_input and not raw_input.startswith("-100"):
        username_part = raw_input.split("t.me/")[-1].replace("+", "").replace("/", "").strip()
        if not raw_input.startswith("https://t.me/+"):
            channel_id = f"@{username_part}"
        suggested_link = raw_input if raw_input.startswith("http") else f"https://{raw_input}"

    try:
        chat = await bot.get_chat(channel_id)
        suggested_name = chat.title or suggested_name
        channel_id = str(chat.id)
        if chat.username:
            suggested_link = f"https://t.me/{chat.username}"
    except Exception:
        pass

    await state.update_data(channel_id=channel_id, suggested_link=suggested_link)
    await state.set_state(AddChannelState.waiting_for_name)
    await message.answer(f"📝 Kanal uchun ko'rinadigan nomni kiriting (Tavsiya: <b>{suggested_name}</b>):", parse_mode="HTML")


@admin_router.message(AddChannelState.waiting_for_name, F.text)
async def add_channel_name(message: Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    suggested_link = data.get("suggested_link", "")

    await state.update_data(channel_name=name)
    await state.set_state(AddChannelState.waiting_for_link)
    hint = f"\n(Masalan: <code>{suggested_link}</code>)" if suggested_link else ""
    await message.answer(f"🔗 Kanalga ulanish havolasini (link) kiriting:{hint}", parse_mode="HTML")


@admin_router.message(AddChannelState.waiting_for_link, F.text)
async def add_channel_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    ch_id = data["channel_id"]
    ch_name = data["channel_name"]
    ch_link = message.text.strip()

    if not ch_link.startswith("http"):
        ch_link = f"https://t.me/{ch_link.replace('@', '')}"

    success = await add_channel(ch_id, ch_name, ch_link)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>{ch_name}</b> kanali muvaffaqiyatli ulandi!\n\n"
            f"🆔 ID: <code>{ch_id}</code>\n"
            f"🔗 Link: {ch_link}",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Kanalni saqlashda xatolik yuz berdi!", reply_markup=get_admin_main_kb())


@admin_router.callback_query(F.data.startswith("del_channel:"))
async def delete_channel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    ch_id = callback.data.split(":", 1)[1]
    success = await delete_channel(ch_id)

    if success:
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
        channels = await get_channels()
        text = "📢 <b>Majburiy obuna kanallari boshqaruvi:</b>\n\n"
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        if channels:
            text += "Ulangan kanallar ro'yxati:\n"
            for ch in channels:
                text += f"🔹 <b>{ch[2]}</b> (<code>{ch[1]}</code>)\n🔗 {ch[3]}\n\n"
                buttons.append([InlineKeyboardButton(text=f"🗑 {ch[2]} ni o'chirish", callback_data=f"del_channel:{ch[1]}")])
        else:
            text += "<i>Hozircha majburiy obuna uchun kanal ulanmagan.</i>\n\n"

        buttons.append([InlineKeyboardButton(text="➕ Yangi kanal/guruh qo'shish", callback_data="add_channel_btn")])
        try:
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
        except Exception:
            pass
    else:
        await callback.answer("❌ Kanal topilmadi!", show_alert=True)


# ==================== XABAR TARQATISH (BROADCAST) ====================

@admin_router.message(F.text == "✉️ Xabar tarqatish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "✉️ Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring (Matn, Rasm, Video yoki Forward):",
        reply_markup=get_cancel_kb()
    )


@admin_router.message(BroadcastState.waiting_for_message)
async def broadcast_process(message: Message, state: FSMContext):
    await state.clear()
    users = await get_all_users()
    
    status_msg = await message.answer(f"⏳ Xabar {len(users)} ta foydalanuvchiga yuborilmoqda...", reply_markup=get_admin_main_kb())

    sent_count = 0
    blocked_count = 0

    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"🟢 Yuborildi: <b>{sent_count} ta</b>\n"
        f"🔴 Yetib bormadi (bloklagan): <b>{blocked_count} ta</b>",
        parse_mode="HTML"
    )
