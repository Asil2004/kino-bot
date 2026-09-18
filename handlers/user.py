from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database import add_user, get_movie, get_channels
from keyboards import get_subscription_kb, get_share_movie_kb
import config

user_router = Router()


async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Foydalanuvchi barcha kanallarga a'zo bo'lganini tekshiradi."""
    # Agar admin bo'lsa tekshirmaydi
    if user_id in config.ADMINS:
        return True, []

    channels = await get_channels()
    # Shuningdek config dagi statik kanal bo'lsa
    all_channels = []
    if config.REQUIRED_CHANNEL:
        all_channels.append((config.REQUIRED_CHANNEL, "Asosiy kanal", config.CHANNEL_URL or "https://t.me"))
    
    for ch in channels:
        # id, channel_id, channel_name, invite_link
        all_channels.append((ch[1], ch[2], ch[3]))

    if not all_channels:
        return True, []

    unsubscribed = []
    for ch_id, ch_name, invite_link in all_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ["left", "kicked"]:
                unsubscribed.append((ch_id, ch_name, invite_link))
        except Exception:
            # Agar bot kanalda admin bo'lmasa yoki xato bersa o'tkazib yuboradi
            pass

    return (len(unsubscribed) == 0), unsubscribed


@user_router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    # Deep linking orqali kod kelgan bo'lsa: /start 105
    args = message.text.split(maxsplit=1)
    movie_code = args[1].strip() if len(args) > 1 else None

    is_subscribed, unsubscribed = await check_user_subscriptions(bot, user.id)

    if not is_subscribed:
        await message.answer(
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Botdan to'liq foydalanish va kinolarni yuklab olish uchun quyidagi kanallarimizga obuna bo'ling:",
            reply_markup=get_subscription_kb(unsubscribed),
            parse_mode="HTML"
        )
        return

    if movie_code:
        await send_movie_by_code(message, bot, movie_code)
    else:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            "🎬 <b>Bugun kinolar botiga xush kelibsiz!</b>\n\n"
            "🔍 Kinoni topish uchun uning <b>kodini yuboring</b> (Masalan: <code>105</code>).",
            parse_mode="HTML"
        )


@user_router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed, unsubscribed = await check_user_subscriptions(bot, user_id)

    if is_subscribed:
        await callback.message.delete()
        await callback.message.answer(
            "✅ <b>Tabriklaymiz, a'zolik tasdiqlandi!</b>\n\n"
            "Endi kino <b>kodini yuborishingiz</b> mumkin (Masalan: <code>105</code>).",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)


async def send_movie_by_code(message: Message, bot: Bot, code: str):
    movie = await get_movie(code)
    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi!\n\n"
            "Iltimos, kodni to'g'ri kiritganingizni tekshiring.",
            parse_mode="HTML"
        )
        return

    bot_info = await bot.get_me()
    caption = movie["caption"] or f"🎬 <b>{movie['title'] or 'Kino'}</b>\n\n🔢 Kodi: <code>{movie['code']}</code>\n👁 Ko'rishlar: {movie['views']}"
    
    caption += f"\n\n🤖 <b>Bizning bot:</b> @{bot_info.username}"

    try:
        await message.answer_video(
            video=movie["file_id"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_share_movie_kb(bot_info.username, movie["code"])
        )
    except Exception as e:
        await message.answer(
            f"❌ Kinoni yuborishda xatolik yuz berdi.\n\n"
            f"🎬 Nomi: {movie['title']}\n🔢 Kodi: <code>{movie['code']}</code>"
        )


@user_router.message(F.text)
async def code_input_handler(message: Message, bot: Bot):
    # Agar admin panel tugmalari bo'lsa, user router ularni ushlamaydi (admin router handles them)
    text = message.text.strip()
    if text.startswith("/"):
        return

    user_id = message.from_user.id
    is_subscribed, unsubscribed = await check_user_subscriptions(bot, user_id)

    if not is_subscribed:
        await message.answer(
            "⚠️ Kinoni yuklash uchun avval quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_subscription_kb(unsubscribed),
            parse_mode="HTML"
        )
        return

    # Kino qidirish
    await send_movie_by_code(message, bot, text)
