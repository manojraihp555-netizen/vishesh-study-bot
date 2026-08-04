import os
from dotenv import load_dotenv

load_dotenv()

# Bot token matching the import in main.py
BOT_TOKEN = os.getenv("TOKEN")

# Parse comma-separated admin IDs safely into a list of integers
ADMIN_IDS = [
    int(i) for i in os.getenv("ADMIN_IDS", "").split(",")
    if i.strip()
]

DB_FILE = "bot_database.db"
