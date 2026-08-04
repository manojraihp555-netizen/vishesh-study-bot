import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [
    int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()
]

DB_FILE = "study_bot.db"
