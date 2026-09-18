# 🎬 Bugun Kinolar Telegram Boti (Kino kodlari orqali kino topuvchi bot)

Ushbu bot foydalanuvchi kino kodini yuborganida unga mos keluvchi kinoni (video, tavsif, ko'rishlar soni) yuboradigan professional Telegram botdir.

---

## ✨ Imkoniyatlari

- 🔍 **Kino kodi orqali qidiruv:** Masalan, foydalanuvchi `105` deb yozsa, `105`-kodli kino video holatida yuboriladi.
- 🔗 **Deep-linking:** `https://t.me/Bugunkinolar_bot?start=105` havolasi orqali kirganda darhol kinoni beradi.
- 👑 **Admin Panel (`/admin`):**
  - 🎬 **Kino qo'shish:** Video yuborish ➡️ Kod belgilash ➡️ Nom berish.
  - 🗑 **Kino o'chirish:** Kod orqali o'chirish.
  - 📊 **Statistika:** Foydalanuvchilar va kinolar soni.
  - 📋 **So'nggi kinolar:** Oxirgi yuklangan kinolar ro'yxati va ularning ko'rishlar soni.
  - 📢 **Kanallarni boshqarish:** Majburiy obuna kanallarini bot ichidan dinamik qo'shish va o'chirish.
  - ✉️ **Xabar tarqatish (Broadcast):** Barcha bot a'zolariga rasm/video/matn xabar yuborish.
- 🛡 **Majburiy obuna tizimi:** Agar kanal kiritilgan bo'lsa, foydalanuvchi obuna bo'lmaguncha kino berilmaydi.

---

## 🚀 Kompyuterni yoqmasdan (GitHub / Bepul Serverda) 24/7 Ishga Tushirish

Loyihani kompyuteringizdan emas, bulutli serverda bepul 24/7 ishlatishning **2 xil oson usuli** mavjud:

---

### 1-USUL: Render.com orqali (ENG TAVSIYA QILINADIGAN, 100% BEPUL 24/7)

1. Ushbu loyiha fayllarini o'zingizning **GitHub** akkauntingizga yangi repozitoriya (Repository) ochib yuklang (Push qiling).
2. [Render.com](https://render.com) saytiga kiring va GitHub profilingiz orqali ro'yxatdan o'ting.
3. **"New +"** tugmasini bosing va **"Background Worker"** (yoki **"Web Service"**) ni tanlang.
4. O'zingizning yuklagan GitHub repozitoriyangizni tanlang.
5. Sozlamalarda:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
6. **"Environment Variables"** (Muhit o'zgaruvchilari) bo'limiga kiring va qo'shing:
   - `BOT_TOKEN` = `8970096817:AAHSNn7uriH_mMCeWjgvvLoh1sYBV39SSAQ`
   - `ADMINS` = `Sizning_Telegram_ID` (Telegramda `@userinfobot` ga yozib o'z ID raqamingizni oling, masalan: `123456789`)
7. **"Create"** tugmasini bosing. Bo'ldi! Bot 24/7 rejimda noutbuksiz o'zi ishlayveradi.

---

### 2-USUL: To'g'ridan-to'g'ri GitHub Actions orqali

1. Loyihani GitHub repozitoriyangizga yuklang.
2. Repozitoriyangizning **Settings** ➡️ **Secrets and variables** ➡️ **Actions** bo'limiga kiring.
3. **"New repository secret"** tugmasini bosib quyidagilarni qo'shing:
   - `BOT_TOKEN` = `8970096817:AAHSNn7uriH_mMCeWjgvvLoh1sYBV39SSAQ`
   - `ADMINS` = `Sizning_Telegram_ID`
4. Repozitoriyaning **Actions** bo'limiga o'tib, **"Telegram Kino Bot 24/7"** workflow-ni bosing va **"Run workflow"** ni ishga tushiring.

---

## 🛠 Admin paneldan foydalanish

1. O'z Telegram ID raqamingizni adminlar ro'yxatiga qo'shing.
2. Botga kiring va `/admin` buyrug'ini yuboring.
3. **"🎬 Kino qo'shish"** tugmasini bosing:
   - Kinoning videosini yuboring;
   - Noyob kod kiriting (masalan: `1`, `105`, `avatar2`);
   - Kino nomini kiriting.
4. Bot sizga tayyor havola va kodni beradi!
