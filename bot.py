import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from database import init_db
from handlers import admin_router, user_router


async def main():
    # Loglarni sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout
    )

    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN aniqlanmadi! .env faylni tekshiring.")
        return

    # Ma'lumotlar bazasini yaratish/tekshirish
    await init_db()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerni ro'yxatdan o'tkazish
    dp.include_router(admin_router)
    dp.include_router(user_router)

    logging.info("Bot muvaffaqiyatli ishga tushirildi!")
    
    # Eski yangilanishlarni o'chirib, yangilarini qabul qilish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
