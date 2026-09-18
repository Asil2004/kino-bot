from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

import config
from database import (
    add_movie, delete_movie, count_movies, count_users, get_all_users,
    get_recent_movies, add_channel, get_channels, delete_channel
)
from keyboards import get_admin_main_kb, get_cancel_kb

admin_router = Router()


# FSM holatlari
class AddMovieState(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_title = State()


class DeleteMovieState(StatesGroup):
    waiting_for_code = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


class AddChannelState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_link = State()


class DeleteChannelState(StatesGroup):
    waiting_for_id = State()


# Admin tekshiruvi filtri
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


# ==================== KINO QO'SHISH ====================

@admin_router.message(F.text == "🎬 Kino qo'shish")
async def start_add_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddMovieState.waiting_for_video)
    await message.answer(
        "📹 Iltimos, kino <b>videosini</b> yoki <b>faylini</b> yuboring:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddMovieState.waiting_for_video, F.video | F.document)
async def process_movie_video(message: Message, state: FSMContext):
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    else:
        await message.answer("Iltimos, video yoki video fayl yuboring!")
        return

    caption = message.caption or ""

    await state.update_data(file_id=file_id, caption=caption)
    await state.set_state(AddMovieState.waiting_for_code)

    await message.answer(
        "🔢 Ushbu kino uchun <b>noyob kod</b> kiriting (Masalan: <code>101</code> yoki <code>marvel-1</code>):",
        parse_mode="HTML"
    )


@admin_router.message(AddMovieState.waiting_for_code, F.text)
async def process_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(code=code)
    await state.set_state(AddMovieState.waiting_for_title)

    await message.answer(
        "📝 Kino nomini kiriting (Masalan: <i>Forsaj 10 (2023)</i>):",
        parse_mode="HTML"
    )


@admin_router.message(AddMovieState.waiting_for_title, F.text)
async def process_movie_title(message: Message, state: FSMContext, bot: Bot):
    title = message.text.strip()
    data = await state.get_data()
    file_id = data["file_id"]
    code = data["code"]
    caption = data.get("caption", "")

    if not caption:
        bot_info = await bot.get_me()
        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"🔢 Kino kodi: <code>{code}</code>\n\n"
            f"🤖 Bot: @{bot_info.username}"
        )

    success = await add_movie(code=code, file_id=file_id, title=title, caption=caption)
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
            f"❌ <b>Xatolik:</b> <code>{code}</code> kodli kino allaqachon mavjud! Boshqa kod bilan urinib ko'ring.",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )


# Tezkor kino qo'shish buyrug'i: /add <kod> <nomi> (video bilan birga yoki videoga reply qilib)
@admin_router.message(Command("add"))
async def quick_add_movie(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    # Reply yoki video xabar tekshiruvi
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
            "Videoni yuborayotganda izohiga (caption) <code>/add 105 Forsaj 10</code> deb yozing yoki videoga javob (reply) tarzida <code>/add 105 Forsaj 10</code> buyrug'ini yuboring.",
            parse_mode="HTML"
        )
        return

    parts = message.text.split(maxsplit=2) if message.text else []
    if len(parts) < 3:
        await message.answer(
            "⚠️ Format noto'g'ri!\nFormat: <code>/add [kod] [kino nomi]</code>\nMasalan: <code>/add 105 Forsaj 10</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    title = parts[2].strip()

    bot_info = await bot.get_me()
    caption = (
        f"🎬 <b>{title}</b>\n\n"
        f"🔢 Kino kodi: <code>{code}</code>\n\n"
        f"🤖 Bot: @{bot_info.username}"
    )

    success = await add_movie(code=code, file_id=file_id, title=title, caption=caption)
    if success:
        await message.answer(
            f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🎬 Nomi: <b>{title}</b>\n"
            f"🔢 Kodi: <code>{code}</code>\n"
            f"🔗 Havola: https://t.me/{bot_info.username}?start={code}",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ <b>Xatolik:</b> <code>{code}</code> kodli kino allaqachon mavjud!",
            parse_mode="HTML"
        )


# ==================== KINO O'CHIRISH ====================

@admin_router.message(F.text == "🗑 Kino o'chirish")
async def start_delete_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(DeleteMovieState.waiting_for_code)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan kinongiz <b>kodini</b> kiriting:",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(DeleteMovieState.waiting_for_code, F.text)
async def process_delete_movie(message: Message, state: FSMContext):
    code = message.text.strip()
    success = await delete_movie(code)
    await state.clear()

    if success:
        await message.answer(f"✅ <code>{code}</code> kodli kino bazadan o'chirildi.", reply_markup=get_admin_main_kb(), parse_mode="HTML")
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
        f"🎬 Bazadagi kinolar: <b>{movies_count} ta</b>",
        parse_mode="HTML"
    )


@admin_router.message(F.text == "📋 So'nggi kinolar")
async def recent_movies_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    movies = await get_recent_movies(limit=15)
    if not movies:
        await message.answer("Bazaga hali kino qo'shilmagan.")
        return

    text = "📋 <b>So'nggi qo'shilgan kinolar:</b>\n\n"
    for code, title, views in movies:
        text += f"🔹 <b>{title or 'Nomsiz'}</b> — Kod: <code>{code}</code> (👁 {views})\n"

    await message.answer(text, parse_mode="HTML")


# ==================== KANALLARNI BOSHQARISH ====================

@admin_router.message(F.text == "📢 Kanallarni boshqarish")
async def manage_channels_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    channels = await get_channels()
    text = "📢 <b>Majburiy obuna kanallari ro'yxati:</b>\n\n"

    if channels:
        for ch in channels:
            # id, channel_id, channel_name, invite_link
            text += f"🆔 <code>{ch[1]}</code> | <b>{ch[2]}</b>\n🔗 {ch[3]}\n\n"
    else:
        text += "<i>Hozircha qo'shimcha majburiy kanal ulanmagan.</i>\n\n"

    text += "Kanal qo'shish uchun: /addchannel\nKanalni o'chirish uchun: /delchannel"
    await message.answer(text, parse_mode="HTML")


@admin_router.message(Command("addchannel"))
async def add_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddChannelState.waiting_for_id)
    await message.answer(
        "Kanal ID sini yoki @username sini kiriting (Masalan: <code>-1001234567890</code> yoki <code>@mening_kanalim</code>):\n\n"
        "<i>Eslatma: Bot ushbu kanalda ADMIN bo'lishi kerak!</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddChannelState.waiting_for_id, F.text)
async def add_channel_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AddChannelState.waiting_for_name)
    await message.answer("Kanal nomini kiriting (Tugmada ko'rinadigan nom):")


@admin_router.message(AddChannelState.waiting_for_name, F.text)
async def add_channel_name(message: Message, state: FSMContext):
    await state.update_data(channel_name=message.text.strip())
    await state.set_state(AddChannelState.waiting_for_link)
    await message.answer("Kanal havolasini kiriting (Masalan: <code>https://t.me/mening_kanalim</code>):", parse_mode="HTML")


@admin_router.message(AddChannelState.waiting_for_link, F.text)
async def add_channel_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    ch_id = data["channel_id"]
    ch_name = data["channel_name"]
    ch_link = message.text.strip()

    success = await add_channel(ch_id, ch_name, ch_link)
    await state.clear()

    if success:
        await message.answer(f"✅ <b>{ch_name}</b> kanali obunalar ro'yxatiga qo'shildi!", reply_markup=get_admin_main_kb(), parse_mode="HTML")
    else:
        await message.answer("❌ Bu kanal allaqachon qo'shilgan!", reply_markup=get_admin_main_kb())


@admin_router.message(Command("delchannel"))
async def del_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(DeleteChannelState.waiting_for_id)
    await message.answer("O'chirmoqchi bo'lgan kanal ID sini kiriting:", reply_markup=get_cancel_kb())


@admin_router.message(DeleteChannelState.waiting_for_id, F.text)
async def del_channel_finish(message: Message, state: FSMContext):
    ch_id = message.text.strip()
    success = await delete_channel(ch_id)
    await state.clear()

    if success:
        await message.answer(f"✅ Kanal ({ch_id}) o'chirildi.", reply_markup=get_admin_main_kb())
    else:
        await message.answer("❌ Kanal topilmadi.", reply_markup=get_admin_main_kb())


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
async def broadcast_process(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await get_all_users()
    
    status_msg = await message.answer(f"⏳ Xabar {len(users)} ta foydalanuvchiga yuborilmoqda...", reply_markup=get_admin_main_kb())

    sent_count = 0
    blocked_count = 0

    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            sent_count += 1
            await asyncio.sleep(0.05)  # Telegram limitlariga tushmaslik uchun
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"🟢 Yuborildi: <b>{sent_count} ta</b>\n"
        f"🔴 Yetib bormadi (bloklagan): <b>{blocked_count} ta</b>",
        parse_mode="HTML"
    )
