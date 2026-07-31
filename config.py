import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_FILE = "database.db"

ADMIN_IDS = [
    8119525298,
]
