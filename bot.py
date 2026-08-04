import logging
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize the database tables
    logger.info("Initializing database...")
    init_db()

    # Build the Telegram application
    logger.info("Starting bot application...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register all bot handlers from handlers.py
    register_handlers(application)

    # Start the Bot using polling
    logger.info("Bot is up and running. Polling started...")
    application.run_polling()

if __name__ == "__main__":
    main()
