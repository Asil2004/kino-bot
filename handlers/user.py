from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext

from database import (
    add_user, get_movie, get_channels, is_user_sub_confirmed, set_user_subscribed,
    get_episodes, get_episode, get_top_movies, get_random_movie_code, get_setting,
    is_admin_user
)
from keyboards import (
    get_subscription_kb, get_share_movie_kb, get_episodes_kb, get_back_to_series_kb,
    get_user_main_kb, get_admin_main_kb
)
import config

user_router = Router()

USER_KEYWORDS = [
    "kino qidirish", "qidiruv", "kino izlash", "search",
    "top kinolar", "top kino", "top",
    "tasodifiy", "random",
    "homiy", "kanallarimiz", "kanallar", "kanal", "obuna", "channels",
    "admin panel", "admin",
    "asosiy menyu", "bosh menyu", "menyu", "menu", "main"
]

ADMIN_KEYWORDS = [
    "bitta film", "kino qo'shish", "kino yuklash", "film qo'shish", "kino qoshish",
    "serial yaratish", "serial qo'shish", "serial yuklash", "serial qoshish",
    "serialga qism", "qism qo'shish", "qism yuklash", "qism qoshish",
    "o'chirish", "ochirish", "kino o'chirish",
    "statistika", "stat",
    "barcha kinolar", "kinolar ro'yxati", "kinolar royxati",
    "kanallarni boshqarish", "kanal boshqaruv", "kanallar sozlamasi",
    "xabar tarqatish", "xabar yuborish", "broadcast",
    "bekor qilish", "bekor", "cancel"
]

GREETING_WORDS = [
    "salom", "assalomu alaykum", "assalom alaykum", "assalamu alaykum",
    "salom aleykum", "privet", "hello", "hi", "hey", "qalesan", "start"
]


def is_system_or_button_text(text: str) -> bool:
    t = text.lower().strip()
    if t.startswith("/"):
        return True
    return any(k in t for k in USER_KEYWORDS + ADMIN_KEYWORDS)


async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list, str, str]:
    """Foydalanuvchi barcha kanallarga a'zo bo'lganini va Instagram tasdiqlanganini tekshiradi."""
    # Agar admin bo'lsa, unga HECH QACHON majburiy obuna chiqmaydi
    if await is_admin_user(user_id):
        return True, [], "", ""

    channels = await get_channels()
    all_channels = []
    
    if getattr(config, "REQUIRED_CHANNEL", None):
        all_channels.append((config.REQUIRED_CHANNEL, "Asosiy kanal", config.CHANNEL_URL or "https://t.me"))
    
    for ch in channels:
        all_channels.append((ch[1], ch[2], ch[3]))

    unsubscribed = []
    for ch_id, ch_name, invite_link in all_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ["left", "kicked"]:
                unsubscribed.append((ch_id, ch_name, invite_link))
        except Exception:
            pass

    insta_url = await get_setting("INSTAGRAM_URL", getattr(config, "INSTAGRAM_URL", ""))
    insta_name = await get_setting("INSTAGRAM_NAME", getattr(config, "INSTAGRAM_NAME", ""))

    if unsubscribed:
        return False, unsubscribed, insta_url, insta_name

    confirmed = await is_user_sub_confirmed(user_id)

    if (all_channels or insta_url) and not confirmed:
        return False, all_channels, insta_url, insta_name

    return True, [], insta_url, insta_name


@user_router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    is_admin = await is_admin_user(user.id)
    args = message.text.split(maxsplit=1)
    movie_code = args[1].strip() if len(args) > 1 else None

    is_subscribed, unsubscribed, insta_url, insta_name = await check_user_subscriptions(bot, user.id)

    if not is_subscribed:
        txt = (
            f"👋 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            "⚠️ Botdan to'liq foydalanish va kinolarni tomosha qilish uchun quyidagi sahifalarimizga obuna bo'ling:\n\n"
            "<i>Obuna bo'lgach, «A'zo bo'ldim / Tekshirish» tugmasini bosing.</i>"
        )
        await message.answer(
            txt,
            reply_markup=get_subscription_kb(
                unsubscribed, movie_code=movie_code, 
                insta_url=insta_url, insta_name=insta_name
            ),
            parse_mode="HTML"
        )
        return

    if movie_code:
        await send_movie_by_code(message, bot, movie_code)
    else:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            "🎬 <b>Bugun kinolar botiga xush kelibsiz!</b>\n\n"
            "🔍 Kinoni topish uchun uning <b>kodini yuboring</b> yoki menyudan kerakli bo'limni tanlang.",
            reply_markup=get_user_main_kb(is_admin=is_admin),
            parse_mode="HTML"
        )


# ==================== ASOSIY MENYU BUYRUQLARI ====================

@user_router.message(F.text.func(lambda t: t and any(w in t.lower() for w in ["asosiy menyu", "bosh menyu", "menyu", "/menu", "/main"])))
async def home_menu_handler(message: Message):
    is_admin = await is_admin_user(message.from_user.id)
    await message.answer(
        "🏠 <b>Asosiy menyu:</b>\nKerakli bo'limni tanlang yoki kino kodini yuboring:",
        reply_markup=get_user_main_kb(is_admin=is_admin),
        parse_mode="HTML"
    )


@user_router.message(F.text.func(lambda t: t and any(w in t.lower() for w in ["kino qidirish", "qidiruv", "kino izlash", "/search"])))
async def search_hint_handler(message: Message):
    await message.answer(
        "🔍 <b>Kino yoki Serialni topish:</b>\n\n"
        "Iltimos, tomosha qilmoqchi bo'lgan filmingiz yoki serialingiz <b>kodini yuboring</b> (Masalan: <code>105</code>).",
        parse_mode="HTML"
    )


@user_router.message(F.text.func(lambda t: t and ("top kinolar" in t.lower() or "top kino" in t.lower() or t.lower().strip() in ["/top", "top", "🔥 top kinolar"])))
async def top_movies_handler(message: Message):
    movies = await get_top_movies(limit=10)
    if not movies:
        await message.answer("Bazaga hali kinolar qo'shilmagan.")
        return

    text = "🔥 <b>Eng ko'p ko'rilgan TOP Kinolar va Seriallar:</b>\n\n"
    for idx, (code, title, m_type, views) in enumerate(movies, start=1):
        icon = "📺" if m_type == "series" else "🎬"
        text += f"{idx}. {icon} <b>{title}</b>\n   🔢 Kodi: <code>{code}</code> (👁 {views} marta ko'rilgan)\n\n"

    text += "<i>Kinoni tomosha qilish uchun uning kodini botga yuboring!</i>"
    await message.answer(text, parse_mode="HTML")


@user_router.message(F.text.func(lambda t: t and any(w in t.lower() for w in ["tasodifiy film", "tasodifiy kino", "tasodifiy", "/tasodifiy", "random"])))
async def random_movie_handler(message: Message, bot: Bot):
    code = await get_random_movie_code()
    if not code:
        await message.answer("Bazaga hali kino qo'shilmagan.")
        return

    await message.answer("🎲 <b>Siz uchun tasodifiy film tanlandi:</b>", parse_mode="HTML")
    await send_movie_by_code(message, bot, code)


@user_router.message(F.text.func(lambda t: t and any(w in t.lower() for w in ["homiy sahifalar", "homiy", "kanallarimiz", "/obuna", "obuna"])))
async def test_subscription_handler(message: Message, bot: Bot):
    channels = await get_channels()
    all_channels = []
    if getattr(config, "REQUIRED_CHANNEL", None):
        all_channels.append((config.REQUIRED_CHANNEL, "Asosiy kanal", config.CHANNEL_URL or "https://t.me"))
    for ch in channels:
        all_channels.append((ch[1], ch[2], ch[3]))

    insta_url = await get_setting("INSTAGRAM_URL", getattr(config, "INSTAGRAM_URL", ""))
    insta_name = await get_setting("INSTAGRAM_NAME", getattr(config, "INSTAGRAM_NAME", ""))

    await message.answer(
        "📢 <b>Bizning rasmiy homiy sahifalarimiz:</b>\n\n"
        "Quyidagi sahifalarga obuna bo'ling:",
        reply_markup=get_subscription_kb(all_channels, insta_url=insta_url, insta_name=insta_name),
        parse_mode="HTML"
    )


@user_router.message(F.text.func(lambda t: t and any(w in t.lower() for w in ["admin panel", "👑 admin panel", "🛠 admin panel", "/admin", "admin"])))
async def admin_button_handler(message: Message):
    if await is_admin_user(message.from_user.id):
        await message.answer("👑 <b>Admin boshqaruv paneli:</b>", reply_markup=get_admin_main_kb(), parse_mode="HTML")
    else:
        await message.answer(f"⚠️ Ushbu bo'lim faqat bot adminlari uchun!\nSizning ID: <code>{message.from_user.id}</code>", parse_mode="HTML")


# ==================== OBUNA CALLBACK ====================

@user_router.callback_query(F.data.startswith("check_sub"))
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_admin = await is_admin_user(user_id)

    parts = callback.data.split(":", 1)
    movie_code = parts[1].strip() if len(parts) > 1 and parts[1].strip() not in ["None", ""] else None

    channels = await get_channels()
    all_channels = []
    if getattr(config, "REQUIRED_CHANNEL", None):
        all_channels.append((config.REQUIRED_CHANNEL, "Asosiy kanal", config.CHANNEL_URL or "https://t.me"))
    for ch in channels:
        all_channels.append((ch[1], ch[2], ch[3]))

    tg_unsubscribed = []
    for ch_id, ch_name, invite_link in all_channels:
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ["left", "kicked"]:
                tg_unsubscribed.append((ch_id, ch_name, invite_link))
        except Exception:
            pass

    insta_url = await get_setting("INSTAGRAM_URL", getattr(config, "INSTAGRAM_URL", ""))
    insta_name = await get_setting("INSTAGRAM_NAME", getattr(config, "INSTAGRAM_NAME", ""))

    if tg_unsubscribed and not is_admin:
        await callback.answer("❌ Siz hali barcha Telegram kanallariga a'zo bo'lmadingiz!", show_alert=True)
        try:
            await callback.message.edit_text(
                "❌ <b>Siz hali barcha kanallarga a'zo bo'lmadingiz!</b>\n\n"
                "Iltimos, quyidagi barcha sahifalarga a'zo bo'ling va so'ngra qayta tekshiring:",
                reply_markup=get_subscription_kb(
                    tg_unsubscribed, movie_code=movie_code,
                    insta_url=insta_url, insta_name=insta_name
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    await set_user_subscribed(user_id, 1)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if movie_code:
        await send_movie_by_code(callback.message, bot, movie_code)
    else:
        await callback.message.answer(
            "✅ <b>Tabriklaymiz, a'zolik tasdiqlandi!</b>\n\n"
            "Endi kino yoki serial <b>kodini yuborishingiz</b> mumkin (Masalan: <code>105</code>).",
            reply_markup=get_user_main_kb(is_admin=is_admin),
            parse_mode="HTML"
        )


async def send_movie_by_code(message: Message, bot: Bot, code: str):
    is_admin = await is_admin_user(message.from_user.id)
    movie = await get_movie(code)
    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino yoki serial topilmadi!\n\n"
            "Iltimos, kodni to'g'ri kiritganingizni tekshiring.",
            reply_markup=get_user_main_kb(is_admin=is_admin),
            parse_mode="HTML"
        )
        return

    bot_info = await bot.get_me()

    # Agar SERIAL bo'lsa
    if movie["movie_type"] == "series":
        episodes = await get_episodes(code)
        
        card_text = (
            f"📺 <b>{movie['title']}</b>\n\n"
            f"🔢 Serial kodi: <code>{movie['code']}</code>\n"
            f"📅 Yili: <b>{movie['year'] or 'Mavjud emas'}</b>\n"
            f"🎭 Janri: <b>{movie['genre'] or 'Mavjud emas'}</b>\n"
            f"🇺🇿 Tili: <b>{movie['language']}</b>\n"
            f"📊 Qismlar soni: <b>{len(episodes)} ta</b>\n"
            f"👁 Ko'rishlar: <b>{movie['views']}</b>\n\n"
        )
        
        if episodes:
            card_text += "👇 <i>Qismni tomosha qilish uchun quyidagi tugmalardan birini tanlang:</i>"
        else:
            card_text += "⚠️ <i>Bu serialga hali qismlar yuklanmagan. Tez orada yuklanadi!</i>"

        card_text += f"\n\n🤖 <b>Bizning bot:</b> @{bot_info.username}"

        keyboard = get_episodes_kb(bot_info.username, movie["code"], episodes)

        if movie["photo_id"]:
            try:
                await message.answer_photo(
                    photo=movie["photo_id"],
                    caption=card_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return
            except Exception:
                pass

        await message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Agar BITTA FILM bo'lsa
    caption = f"🎬 <b>{movie['title']}</b>\n\n🔢 Kino kodi: <code>{movie['code']}</code>\n👁 Ko'rishlar: {movie['views']}\n\n🤖 <b>Bizning bot:</b> @{bot_info.username}"

    try:
        await message.answer_video(
            video=movie["file_id"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_share_movie_kb(bot_info.username, movie["code"])
        )
    except Exception:
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


@user_router.callback_query(F.data.startswith("show_ep:"))
async def show_episode_callback(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    movie_code = parts[1]
    ep_num = int(parts[2])

    movie = await get_movie(movie_code)
    ep = await get_episode(movie_code, ep_num)

    if not ep:
        await callback.answer(f"❌ {ep_num}-qism hali yuklanmagan!", show_alert=True)
        return

    bot_info = await bot.get_me()
    title = movie["title"] if movie else "Serial"
    caption = (
        f"🎬 <b>{title} — {ep_num}-qism</b>\n\n"
        f"🔢 Serial kodi: <code>{movie_code}</code>\n"
        f"👁 Ko'rishlar: {ep['views']}\n\n"
        f"🤖 <b>Bizning bot:</b> @{bot_info.username}"
    )

    await callback.answer(f"▶️ {ep_num}-qism yuklanmoqda...")

    try:
        await callback.message.answer_video(
            video=ep["file_id"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_back_to_series_kb(movie_code, bot_info.username)
        )
    except Exception:
        try:
            await callback.message.answer_document(
                document=ep["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_back_to_series_kb(movie_code, bot_info.username)
            )
        except Exception:
            await callback.message.answer("⚠️ Videoni yuborishda xatolik yuz berdi.")


@user_router.callback_query(F.data.startswith("ep_page:"))
async def change_episode_page_callback(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    movie_code = parts[1]
    page = int(parts[2])

    episodes = await get_episodes(movie_code)
    bot_info = await bot.get_me()
    new_kb = get_episodes_kb(bot_info.username, movie_code, episodes, page=page)

    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass
    await callback.answer()


@user_router.callback_query(F.data.startswith("show_series:"))
async def show_series_callback(callback: CallbackQuery, bot: Bot):
    movie_code = callback.data.split(":", 1)[1]
    await send_movie_by_code(callback.message, bot, movie_code)
    await callback.answer()


@user_router.message(StateFilter(None), F.text)
async def code_input_handler(message: Message, state: FSMContext, bot: Bot):
    # Agar admin yoki foydalanuvchi biror FSM holatida (wizardda) bo'lsa kino qidirmaymiz
    cur_state = await state.get_state()
    if cur_state is not None:
        return

    text = message.text.strip()
    
    # Agar komanda yoki menyu/admin tugmasi bo'lsa kod deb qidirmaymiz
    if is_system_or_button_text(text):
        return

    user_id = message.from_user.id
    is_admin = await is_admin_user(user_id)

    # Agar foydalanuvchi ADMIN bo'lsa, u kino qidirmaydi (adminga xato bermasdan admin panel ko'rsatiladi)
    if is_admin:
        await message.answer(
            "👑 <b>Admin boshqaruv paneli:</b>\n\n"
            "Kino yoki serial yuklash, o'chirish yoki sozlamalar uchun quyidagi tugmalardan birini tanlang:\n\n"
            "📹 <i>Shuningdek, istalgan video yoki faylni botga tashlasangiz, avtomatik kino sifatida yuklanadi!</i>",
            reply_markup=get_admin_main_kb(),
            parse_mode="HTML"
        )
        return

    # Agar salomlashish yoki umumiy so'z bo'lsa, xush kelibsiz xabarini chiqaramiz
    if text.lower() in GREETING_WORDS:
        await message.answer(
            f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
            "🔍 Kinoni tomosha qilish uchun uning <b>kodini yuboring</b> (Masalan: <code>105</code>) yoki quyidagi menyudan foydalaning.",
            reply_markup=get_user_main_kb(is_admin=is_admin),
            parse_mode="HTML"
        )
        return

    is_subscribed, unsubscribed, insta_url, insta_name = await check_user_subscriptions(bot, user_id)

    if not is_subscribed:
        await message.answer(
            f"⚠️ <b>«{text}» kodli kinoni tomosha qilish uchun quyidagi sahifalarimizga obuna bo'ling:</b>\n\n"
            "<i>Obuna bo'lib, «A'zo bo'ldim / Tekshirish» tugmasini bosing. Kino avtomatik yuboriladi!</i>",
            reply_markup=get_subscription_kb(
                unsubscribed, movie_code=text,
                insta_url=insta_url, insta_name=insta_name
            ),
            parse_mode="HTML"
        )
        return

    await send_movie_by_code(message, bot, text)
