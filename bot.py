import logging
from telegram.ext import ApplicationBuilder, CommandHandler

from config import TOKEN
from database import init_db
from handlers import (
    start,
    help_command,
    myid,
    add_note_conv_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    init_db()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid))

    application.add_handler(add_note_conv_handler)

    logger.info("Vishesh Study Bot Started...")
    application.run_polling()


if __name__ == "__main__":
    main()
