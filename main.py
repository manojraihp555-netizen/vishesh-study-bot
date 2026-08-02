from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import TOKEN
from handlers import (
    start,
    help_command,
    myid,
    allnotes,
    broadcast_start,
    handle_direct_message,
    add_note_conv_handler,
    delete_note_conv_handler,
    note_conv_handler,
    edit_note_conv_handler,
)
from database import init_db

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("allnotes", allnotes))
    app.add_handler(CommandHandler("broadcast", broadcast_start))

    # Conversation Handlers
    app.add_handler(add_note_conv_handler)
    app.add_handler(delete_note_conv_handler)
    app.add_handler(note_conv_handler)
    app.add_handler(edit_note_conv_handler)

    # Direct AI Chat Message Handler (Must be at the end)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_message))

    print("Bot is running with AI and Broadcast features...")
    app.run_polling()

if __name__ == "__main__":
    main()
