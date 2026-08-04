import os
from import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database
DATABASE_NAME = "study_bot.db"

# Admin IDs (Multiple admins supported)
ADMIN_IDS = [
    int(admin_id)
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip()
] import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [
    int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()
]

DB_FILE = "study_bot.db"
