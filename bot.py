import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)

from config import TOKEN
from database import init_db
from handlers import start, help_command

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    # Database initialize
    init_db()

    # Bot application
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("Vishesh Study Bot Started...")

    app.run_polling()


if __name__ == "__main__":
    main()
