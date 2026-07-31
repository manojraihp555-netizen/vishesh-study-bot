from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from admin import is_admin
from database import add_note

# Define conversation states
CLASS, SUBJECT, TOPIC, FILE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Existing /start command handler."""
    await update.message.reply_text(
        "📚 Welcome to Vishesh Study Bot!\n\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Existing /help command handler."""
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

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Existing /myid command handler."""
    await update.message.reply_text(
        f"🆔 Your Telegram ID: {update.effective_user.id}"
    )

# --- Add Note Conversation Handlers ---

async def addnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /addnote command."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return ConversationHandler.END

    # Clear any leftover data
    context.user_data.clear()
    
    await update.message.reply_text("📚 Enter Class:")
    return CLASS

async def received_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store class and ask for subject."""
    context.user_data["class"] = update.message.text.strip()
    await update.message.reply_text("📖 Enter Subject:")
    return SUBJECT

async def received_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store subject and ask for topic."""
    context.user_data["subject"] = update.message.text.strip()
    await update.message.reply_text("📝 Enter Topic:")
    return TOPIC

async def received_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store topic and ask for file."""
    context.user_data["topic"] = update.message.text.strip()
    await update.message.reply_text("📎 Send PDF or Photo:")
    return FILE

async def received_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle incoming file (PDF document or Photo), save to DB, and end conversation."""
    message = update.message
    file_id = None
    file_name = None
    file_type = None

    if message.document and message.document.mime_type == "application/pdf":
        file_id = message.document.file_id
        file_name = message.document.file_name or "document.pdf"
        file_type = "document"
    elif message.photo:
        # Get the largest photo
        largest_photo = message.photo[-1]
        file_id = largest_photo.file_id
        file_name = "Photo"
        file_type = "photo"
    else:
        await message.reply_text("❌ Please send only PDF or Photo.")
        return FILE

    # Retrieve stored data
    student_class = context.user_data.get("class")
    subject = context.user_data.get("subject")
    topic = context.user_data.get("topic")

    # Save using the existing add_note function
    add_note(
        student_class,
        subject,
        topic,
        file_id,
        file_type,
        file_name
    )

    await message.reply_text(
        f"✅ Note Added Successfully!\n\n"
        f"📚 Class: {student_class}\n"
        f"📖 Subject: {subject}\n"
        f"📝 Topic: {topic}"
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Operation Cancelled.")
    return ConversationHandler.END

# Define the ConversationHandler to be imported in bot.py
add_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("addnote", addnote_start)],
    states={
        CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_class)],
        SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_subject)],
        TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_topic)],
        FILE: [
            MessageHandler(
                (filters.Document.PDF | filters.PHOTO | filters.TEXT) & ~filters.COMMAND,
                received_file,
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
