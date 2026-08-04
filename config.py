import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("TOKEN")

# Database
DATABASE_NAME = "study_bot.db"

# Admin IDs
ADMIN_IDS = [
    int(i)
    for i in os.getenv("ADMIN_IDS", "").split(",")
    if i.strip()
]
