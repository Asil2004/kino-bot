from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import add_user, get_movie, get_channels
from keyboards import get_subscription_kb, get_share_movie_kb
import config

user_router = Router()


async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Foydalanuvchi barcha kanallarga a'zo bo'lganini tekshiradi."""
    # Agar admin bo'lsa majburiy obunani tekshirmaydi
    if user_id in config.ADMINS:
        return True, []

    channels = await get_channels()
    all_channels = []
    
    # config.py dagi statik kanal bo'lsa
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
            # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa foydalanuvchini to'xtatmaydi
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
        txt = (
            f"👋 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            "⚠️ Botdan to'liq foydalanish va kinoni yuklab olish uchun quyidagi kanallarga obuna bo'ling:\n\n"
            "<i>Obuna bo'lgach, «A'zo bo'ldim / Tekshirish» tugmasini bosing.</i>"
        )
        await message.answer(
            txt,
            reply_markup=get_subscription_kb(unsubscribed, movie_code=movie_code),
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


@user_router.callback_query(F.data.startswith("check_sub"))
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    # Callback ma'lumotidan kino kodini olish
    parts = callback.data.split(":", 1)
    movie_code = parts[1].strip() if len(parts) > 1 and parts[1].strip() != "None" else None

    is_subscribed, unsubscribed = await check_user_subscriptions(bot, user_id)

    if is_subscribed:
        try:
            await callback.message.delete()
        except Exception:
            pass

        if movie_code:
            await callback.message.answer("✅ <b>A'zoligingiz tasdiqlandi! Kino yuklanmoqda...</b>", parse_mode="HTML")
            await send_movie_by_code(callback.message, bot, movie_code)
        else:
            await callback.message.answer(
                "✅ <b>Tabriklaymiz, a'zolik tasdiqlandi!</b>\n\n"
                "Endi kino <b>kodini yuborishingiz</b> mumkin (Masalan: <code>105</code>).",
                parse_mode="HTML"
            )
    else:
        # A'zo bo'lmaguncha qayta so'raydi va ogohlantiradi
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, barcha kanallarga a'zo bo'ling.", show_alert=True)
        try:
            await callback.message.edit_text(
                "❌ <b>Siz hali barcha kanallarga a'zo bo'lmadingiz!</b>\n\n"
                "Iltimos, quyidagi barcha kanallarga a'zo bo'ling va so'ngra qayta tekshiring:",
                reply_markup=get_subscription_kb(unsubscribed, movie_code=movie_code),
                parse_mode="HTML"
            )
        except Exception:
            pass


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
    except Exception:
        # Video fayl sifatida yuborilgan bo'lsa
        try:
            await message.answer_document(
                document=movie["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_share_movie_kb(bot_info.username, movie["code"])
            )
        except Exception:
            await message.answer(
                f"🎬 <b>{movie['title']}</b>\n🔢 Kodi: <code>{movie['code']}</code>\n\n⚠️ Kinoni yuklashda xatolik yuz berdi.",
                parse_mode="HTML"
            )


@user_router.message(F.text)
async def code_input_handler(message: Message, bot: Bot):
    text = message.text.strip()
    if text.startswith("/"):
        return

    user_id = message.from_user.id
    is_subscribed, unsubscribed = await check_user_subscriptions(bot, user_id)

    if not is_subscribed:
        await message.answer(
            f"⚠️ <b>«{text}» kodli kinoni yuklab olish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            "<i>Obuna bo'lib, «A'zo bo'ldim / Tekshirish» tugmasini bosing. Kino avtomatik yuboriladi!</i>",
            reply_markup=get_subscription_kb(unsubscribed, movie_code=text),
            parse_mode="HTML"
        )
        return

    # Kino qidirish
    await send_movie_by_code(message, bot, text)
