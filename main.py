import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from handlers import register_handlers
from database import init_db

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Bot Token from environment variable or set fallback
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

async def error_handler(update, context):
    """Global error handler to prevent bot crash on unhandled exceptions."""
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN missing! Please set your token in .env or main.py")
        return

    # 1. Initialize SQLite Database tables
    init_db()
    logger.info("✅ Database initialized successfully.")

    # 2. Build python-telegram-bot Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 3. Register command and message handlers
    register_handlers(application)
    logger.info("✅ All handlers registered successfully.")

    # 4. Add global error handler
    application.add_error_handler(error_handler)

    # 5. Start Polling
    logger.info("🚀 Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
