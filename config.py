import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8970096817:AAHSNn7uriH_mMCeWjgvvLoh1sYBV39SSAQ")

# Adminlar ro'yxati (vergul bilan ajratilgan IDlar: masalan "12345678,98765432")
admins_raw = os.getenv("ADMINS", "")
ADMINS = [int(admin_id.strip()) for admin_id in admins_raw.split(",") if admin_id.strip().isdigit()]

# Majburiy obuna kanallari
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "").strip()
