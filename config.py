import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8970096817:AAGVfnFLB6JnI7hJkZNIjwqFjXLUg3AAu3k")

# Adminlar ro'yxati (vergul bilan ajratilgan IDlar: masalan "7747943559,1044882545")
admins_raw = os.getenv("ADMINS", "7747943559,1044882545")
ADMINS = [int(admin_id.strip()) for admin_id in admins_raw.split(",") if admin_id.strip().isdigit()]
for aid in [7747943559, 1044882545]:
    if aid not in ADMINS:
        ADMINS.append(aid)

# Majburiy obuna kanallari
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()

# Instagram sahifasi
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/asilbek_ravshanov04").strip()
INSTAGRAM_NAME = os.getenv("INSTAGRAM_NAME", "asilbek_ravshanov04").strip()
