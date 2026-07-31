from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Welcome to Vishesh Study Bot!\n\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Available Commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/note - Search notes\n"
        "/allnotes - View all notes\n"
        "/addnote - Add a note (Admin)\n"
        "/deletenote - Delete a note (Admin)"
    )
