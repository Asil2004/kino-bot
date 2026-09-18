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
    text = "📢 <b>Majburiy obuna kanallari boshqaruvi:</b>\n\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []

    if channels:
        text += "Ulangan kanallar ro'yxati:\n"
        for ch in channels:
            # id, channel_id, channel_name, invite_link
            text += f"🔹 <b>{ch[2]}</b> (<code>{ch[1]}</code>)\n🔗 {ch[3]}\n\n"
            buttons.append([
                InlineKeyboardButton(text=f"🗑 {ch[2]} ni o'chirish", callback_data=f"del_channel:{ch[1]}")
            ])
    else:
        text += "<i>Hozircha majburiy obuna uchun kanal ulanmagan.</i>\n\n"

    buttons.append([InlineKeyboardButton(text="➕ Yangi kanal/guruh qo'shish", callback_data="add_channel_btn")])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")


@admin_router.callback_query(F.data == "add_channel_btn")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AddChannelState.waiting_for_id)
    await callback.message.answer(
        "📢 <b>Kanal yoki Guruhni ulash:</b>\n\n"
        "Kanal username (@kanal_nomi), havolasi (https://t.me/...) yoki ID raqamini kiriting:\n\n"
        "⚠️ <b>MUHIM:</b> Bot ushbu kanalda/guruhda <b>ADMIN</b> bo'lishi kerak, aks holda a'zolikni tekshira olmaydi!",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(Command("addchannel"))
async def add_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AddChannelState.waiting_for_id)
    await message.answer(
        "📢 Kanal username (@kanal_nomi), havolasi yoki ID raqamini kiriting:\n\n"
        "<i>Eslatma: Bot ushbu kanalda ADMIN bo'lishi shart!</i>",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )


@admin_router.message(AddChannelState.waiting_for_id, F.text)
async def add_channel_id(message: Message, state: FSMContext, bot: Bot):
    raw_input = message.text.strip()
    
    # Havoladan username ajratib olish (agar havola yuborilgan bo'lsa)
    channel_id = raw_input
    suggested_link = raw_input
    suggested_name = "Kanal"

    if "t.me/" in raw_input and not raw_input.startswith("-100"):
        username_part = raw_input.split("t.me/")[-1].replace("+", "").replace("/", "").strip()
        if not raw_input.startswith("https://t.me/+"):
            channel_id = f"@{username_part}"
        suggested_link = raw_input if raw_input.startswith("http") else f"https://{raw_input}"

    # Telegram orqali kanal nomini tekshirib ko'rish
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
    await message.answer(
        f"📝 Kanal uchun ko'rinadigan nomni kiriting (Tavsiya: <b>{suggested_name}</b>):",
        parse_mode="HTML"
    )


@admin_router.message(AddChannelState.waiting_for_name, F.text)
async def add_channel_name(message: Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    suggested_link = data.get("suggested_link", "")

    await state.update_data(channel_name=name)
    await state.set_state(AddChannelState.waiting_for_link)
    
    hint = f"\n(Masalan: <code>{suggested_link}</code>)" if suggested_link else ""
    await message.answer(
        f"🔗 Kanalga ulanish havolasini (link) kiriting:{hint}",
        parse_mode="HTML"
    )


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
            f"🔗 Link: {ch_link}\n\n"
            f"Endi foydalanuvchilar ushbu kanalga obuna bo'lmaguncha kino yuklay olmaydi.",
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
        # Menuni yangilash
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
        await message.answer(f"✅ Kanal (<code>{ch_id}</code>) o'chirildi.", reply_markup=get_admin_main_kb(), parse_mode="HTML")
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
