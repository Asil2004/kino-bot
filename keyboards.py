from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


# Admin asosiy menyusi
def get_admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="🗑 Kino o'chirish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📋 So'nggi kinolar")],
            [KeyboardButton(text="📢 Kanallarni boshqarish"), KeyboardButton(text="✉️ Xabar tarqatish")],
        ],
        resize_keyboard=True
    )


# Bekor qilish tugmasi
def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


# Majburiy obuna inline tugmalari
def get_subscription_kb(channels: list, movie_code: str | None = None) -> InlineKeyboardMarkup:
    buttons = []
    for idx, (ch_id, ch_name, invite_link) in enumerate(channels, start=1):
        name = ch_name or f"Kanal #{idx}"
        buttons.append([InlineKeyboardButton(text=f"➕ {name}", url=invite_link)])
    
    cb_data = f"check_sub:{movie_code}" if movie_code else "check_sub"
    buttons.append([InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data=cb_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Kino ulashish tugmasi
def get_share_movie_kb(bot_username: str, movie_code: str) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text=🎬 Kinoni tomosha qiling! Kod: {movie_code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)]
        ]
    )
