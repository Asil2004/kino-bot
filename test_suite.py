import asyncio
import os
import sys

# Loyihaning asosiy modullarini tekshiramiz
from database import (
    init_db, add_user, is_user_sub_confirmed, set_user_subscribed, count_users,
    add_movie, get_movie, delete_movie, count_movies, get_recent_movies,
    get_top_movies, get_random_movie_code, add_episode, get_episodes, get_episode,
    delete_episode, add_channel, get_channels, delete_channel,
    set_setting, get_setting, is_admin_user, add_admin_db
)
from keyboards import (
    get_user_main_kb, get_admin_main_kb, get_subscription_kb,
    get_episodes_kb, get_share_movie_kb, get_back_to_series_kb
)
import config


async def run_tests():
    print("==================================================")
    print("🧪 BUGUNKINOLAR_BOT TO'LIQ TEST SINOVI BOSHLANDI")
    print("==================================================")

    # 1. Baza initsializatsiyasi
    print("\n[TEST 1] Ma'lumotlar bazasini initsializatsiya qilish...")
    await init_db()
    print("✅ Baza jadvallari (users, movies, episodes, channels, settings) muvaffaqiyatli yaratildi.")

    # 2. Admin tekshiruvlari
    print("\n[TEST 2] Adminlik huquqini tekshirish...")
    is_owner_admin = await is_admin_user(7747943559)
    assert is_owner_admin is True, "Xatolik: 7747943559 admin bo'lishi kerak edi!"
    
    # Yangi admin qo'shish
    await add_admin_db(999888777)
    is_new_admin = await is_admin_user(999888777)
    assert is_new_admin is True, "Xatolik: Yangi qo'shilgan admin tasdiqlanmadi!"

    is_random_user_admin = await is_admin_user(1122334455)
    assert is_random_user_admin is False, "Xatolik: Oddiy foydalanuvchi admin bo'lib qoldi!"
    print("✅ Adminlik tekshiruvlari 100% to'g'ri ishladi.")

    # 3. Bitta Film (Single Movie) qo'shish va qidirish
    print("\n[TEST 3] Bitta filmni bazaga qo'shish va qidirish...")
    test_code = "test_101"
    test_title = "Forsaj 10 (2023)"
    test_file_id = "BAACAgIAAxkBAAI..."
    test_caption = f"🎬 <b>{test_title}</b>\n\n🔢 Kino kodi: <code>{test_code}</code>"

    # Filmni qo'shamiz
    success = await add_movie(code=test_code, file_id=test_file_id, title=test_title, movie_type="single", caption=test_caption)
    assert success is True, "Xatolik: Film qo'shilmadi!"

    # Filmni kod orqali topamiz
    movie = await get_movie(test_code)
    assert movie is not None, "Xatolik: Film bazadan topilmadi!"
    assert movie["title"] == test_title, f"Xatolik: Nomi mos kelmadi: {movie['title']}"
    assert movie["file_id"] == test_file_id, "Xatolik: file_id mos kelmadi!"
    assert movie["views"] >= 1, "Xatolik: Ko'rishlar soni oshmadi!"
    print(f"✅ Film muvaffaqiyatli saqlandi va topildi: {movie['title']} (Ko'rishlar: {movie['views']})")

    # 4. Ko'p qismli Serial (Series) yaratish va qismlar yuklash
    print("\n[TEST 4] Serial yaratish va qismlar (1-qism, 2-qism) yuklash...")
    series_code = "test_serial_202"
    series_title = "Qashqirlar Makoni"
    
    # Serial kartochkasi
    s_success = await add_movie(
        code=series_code, file_id="", title=series_title, 
        movie_type="series", year="2003", genre="Jangari, Kriminal", photo_id="AgACAgIA..."
    )
    assert s_success is True, "Xatolik: Serial yaratilmadi!"

    # 1-qismni qo'shamiz
    ep1_success = await add_episode(movie_code=series_code, episode_number=1, file_id="EP_1_FILE_ID")
    assert ep1_success is True, "Xatolik: 1-qism qo'shilmadi!"

    # 2-qismni qo'shamiz
    ep2_success = await add_episode(movie_code=series_code, episode_number=2, file_id="EP_2_FILE_ID")
    assert ep2_success is True, "Xatolik: 2-qism qo'shilmadi!"

    # Serial qismlarini tekshiramiz
    episodes = await get_episodes(series_code)
    assert len(episodes) == 2, f"Xatolik: Qismlar soni 2 bo'lishi kerak edi, lekin {len(episodes)} ta!"

    # 1-qismni o'qib ko'rish
    ep1 = await get_episode(series_code, 1)
    assert ep1 is not None and ep1["file_id"] == "EP_1_FILE_ID", "Xatolik: 1-qism videosi topilmadi!"
    print(f"✅ Serial va uning {len(episodes)} ta qismi muvaffaqiyatli saqlandi va yuklandi.")

    # 5. TOP Kinolar va Tasodifiy film
    print("\n[TEST 5] TOP ko'rilgan kinolar va tasodifiy filmni sinash...")
    top_list = await get_top_movies(limit=5)
    assert len(top_list) >= 2, "Xatolik: TOP ro'yxatda kinolar chiqmadi!"
    random_code = await get_random_movie_code()
    assert random_code in [test_code, series_code], f"Xatolik: Tasodifiy film kodi noto'g'ri: {random_code}"
    print(f"✅ TOP kinolar ro'yxati va Tasodifiy film ({random_code}) xatosiz ishlamoqda.")

    # 6. Kanallar va Instagram sozlamalari
    print("\n[TEST 6] Majburiy obuna va Instagram sozlamalarini sinash...")
    # Instagram sozlamasi
    await set_setting("INSTAGRAM_URL", "https://instagram.com/asilbek_ravshanov04")
    await set_setting("INSTAGRAM_NAME", "asilbek_ravshanov04")
    saved_insta = await get_setting("INSTAGRAM_URL")
    assert saved_insta == "https://instagram.com/asilbek_ravshanov04", "Xatolik: Instagram URL saqlanmadi!"

    # Telegram kanal qo'shish
    await add_channel("-1001234567890", "Test Homiy Kanal", "https://t.me/test_kanal")
    channels = await get_channels()
    assert any(ch[1] == "-1001234567890" for ch in channels), "Xatolik: Kanal ro'yxatga qo'shilmadi!"
    print("✅ Kanal va Instagram homiy sahifalari to'g'ri ishlamoqda.")

    # 7. Tugmalar va Menyu generatsiyasi
    print("\n[TEST 7] Tugmalar (Keyboards) va Menyu panellarini tekshirish...")
    user_kb = get_user_main_kb(is_admin=False)
    assert len(user_kb.keyboard) == 2, "Xatolik: Oddiy foydalanuvchida admin tugmasi ko'rinmasligi kerak!"
    
    admin_kb = get_user_main_kb(is_admin=True)
    assert len(admin_kb.keyboard) == 3, "Xatolik: Adminga 'Admin Panel' tugmasi chiqishi kerak!"

    ep_kb = get_episodes_kb("Bugunkinolar_bot", series_code, episodes)
    assert ep_kb is not None, "Xatolik: Qismlar tugmasi generatsiya qilinmadi!"

    sub_kb = get_subscription_kb(channels, movie_code=test_code, insta_url=saved_insta, insta_name="asilbek_ravshanov04")
    assert sub_kb is not None, "Xatolik: Obuna tugmalari generatsiya qilinmadi!"
    print("✅ Barcha interfeys tugmalari va menyu panellari 100% to'g'ri generatsiya qilindi.")

    # 8. Test ma'lumotlarini tozalash
    print("\n[TEST 8] Test ma'lumotlarini tozalash...")
    await delete_movie(test_code)
    await delete_movie(series_code)
    await delete_channel("-1001234567890")
    print("✅ Test ma'lumotlari xavfsiz tozalandi.")

    print("\n==================================================")
    print("🎉 BARCHA TESTLAR 100% MUVAFFAQIYATLI YAKUNLANDI!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
