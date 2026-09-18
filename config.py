import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8970096817:AAHSNn7uriH_mMCeWjgvvLoh1sYBV39SSAQ")

# Adminlar ro'yxati (vergul bilan ajratilgan IDlar: masalan "7747943559,12345678")
admins_raw = os.getenv("ADMINS", "7747943559")
ADMINS = [int(admin_id.strip()) for admin_id in admins_raw.split(",") if admin_id.strip().isdigit()]
if 7747943559 not in ADMINS:
    ADMINS.append(7747943559)

# Majburiy obuna kanallari
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()

# Instagram sahifasi
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/asilbek_ravshanov04").strip()
INSTAGRAM_NAME = os.getenv("INSTAGRAM_NAME", "asilbek_ravshanov04").strip()
