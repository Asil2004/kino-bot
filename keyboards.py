from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import config


# Admin asosiy menyusi
def get_admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Bitta Film qo'shish"), KeyboardButton(text="📺 Serial / Anime yaratish")],
            [KeyboardButton(text="➕ Serialga qism qo'shish"), KeyboardButton(text="🗑 O'chirish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📋 Barcha kinolar")],
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
    
    # Instagram sahifasi
    if getattr(config, "INSTAGRAM_URL", None):
        insta_label = f"📸 Instagram: @{config.INSTAGRAM_NAME}" if getattr(config, "INSTAGRAM_NAME", None) else "📸 Instagram sahifamiz"
        buttons.append([InlineKeyboardButton(text=insta_label, url=config.INSTAGRAM_URL)])

    # Telegram kanallari
    for idx, (ch_id, ch_name, invite_link) in enumerate(channels, start=1):
        name = ch_name or f"Kanal #{idx}"
        buttons.append([InlineKeyboardButton(text=f"➕ {name}", url=invite_link)])
    
    cb_data = f"check_sub:{movie_code}" if movie_code else "check_sub"
    buttons.append([InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data=cb_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Serial qismlari tugmalari (Grid ko'rinishida)
def get_episodes_kb(bot_username: str, movie_code: str, episodes: list, page: int = 1, per_page: int = 20) -> InlineKeyboardMarkup:
    buttons = []
    total_eps = len(episodes)
    
    # Sahifalash (Pagination)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_eps = episodes[start_idx:end_idx]

    # Qismlarni 4 tadan qator qilib joylashtirish
    row = []
    for ep in current_eps:
        # ep: (episode_number, title, views)
        ep_num = ep[0]
        row.append(InlineKeyboardButton(text=f"{ep_num}-qism", callback_data=f"show_ep:{movie_code}:{ep_num}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Oldingi / Keyingi tugmalari
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"ep_page:{movie_code}:{page-1}"))
    if end_idx < total_eps:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"ep_page:{movie_code}:{page+1}"))
    if nav_row:
        buttons.append(nav_row)

    # Ulashish tugmasi
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text=🎬 Kinoni tomosha qiling! Kod: {movie_code}"
    buttons.append([InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Qismdan serial asosiy kartochkasiga qaytish tugmasi
def get_back_to_series_kb(movie_code: str, bot_username: str) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text=🎬 Kinoni tomosha qiling! Kod: {movie_code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Barcha qismlar ro'yxati", callback_data=f"show_series:{movie_code}")],
            [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)]
        ]
    )


# Bitta kino ulashish tugmasi
def get_share_movie_kb(bot_username: str, movie_code: str) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start={movie_code}&text=🎬 Kinoni tomosha qiling! Kod: {movie_code}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)]
        ]
    )
