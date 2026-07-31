from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from admin import is_admin

# Conversation States
CLASS, SUBJECT, TOPIC, FILE = range(4)


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
        "/deletenote - Delete a note (Admin)\n"
        "/myid - Get your Telegram ID"
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Your Telegram ID: {update.effective_user.id}"
    )


async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized to use this command."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📚 Enter Class:"
    )

    return CLASS


async def get_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["class"] = update.message.text

    await update.message.reply_text(
        "📖 Enter Subject:"
    )

    return SUBJECT


async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["subject"] = update.message.text

    await update.message.reply_text(
        "📝 Enter Topic:"
    )

    return TOPIC
