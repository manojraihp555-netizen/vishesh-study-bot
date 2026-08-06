import os
from dotenv import load_dotenv

load_dotenv()

# Bot token env variable updated to BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Parse comma-separated admin IDs safely into a list of integers
ADMIN_IDS = [
    int(i) for i in os.getenv("ADMIN_IDS", "").split(",")
    if i.strip()
]

# Updated database filename to match database.py
DB_FILE = "bot_data.db"

