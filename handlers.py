from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from database import (
    add_note,
    delete_note,
    search_notes,
    get_all_notes,
    update_note,
)

from admin import is_admin
# ===== ADD NOTE =====
CLASS = 0
SUBJECT = 1
TOPIC = 2
FILE = 3

# ===== DELETE NOTE =====
DELETE_TOPIC = 4

# ===== SEARCH =====
SEARCH_QUERY = 100

# ===== EDIT =====
EDIT_OLD_TOPIC = 101
EDIT_NEW_CLASS = 102
EDIT_NEW_SUBJECT = 103
EDIT_NEW_TOPIC = 104
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Vishesh Study Bot!\n\n"
        "Use /help to see all commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Available Commands\n\n"
        "/start\n"
        "/help\n"
        "/myid\n"
        "/note\n"
        "/allnotes\n\n"
        "Admin Commands:\n"
        "/addnote\n"
        "/deletenote\n"
        "/editnote"
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Your Telegram ID:\n{update.effective_user.id}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END
    # ==========================================
# ADD NOTE
# ==========================================

async def addnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text("📚 Enter Class")
    return CLASS


async def received_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["class"] = update.message.text.strip()
    await update.message.reply_text("📖 Enter Subject")
    return SUBJECT


async def received_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["subject"] = update.message.text.strip()
    await update.message.reply_text("📝 Enter Topic")
    return TOPIC


async def received_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["topic"] = update.message.text.strip()
    await update.message.reply_text("📎 Send Document or Photo")
    return FILE


async def received_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    file_id = None
    file_type = None
    file_name = ""

    if update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
        file_name = update.message.document.file_name

    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        file_name = "Photo"

    else:
        await update.message.reply_text("❌ Send a Document or Photo only.")
        return FILE

    add_note(
        context.user_data["class"],
        context.user_data["subject"],
        context.user_data["topic"],
        file_id,
        file_type,
        file_name,
    )

    await update.message.reply_text("✅ Note Added Successfully.")

    context.user_data.clear()

    return ConversationHandler.END
    # ==========================================
# DELETE NOTE
# ==========================================

async def deletenote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text("🗑 Enter Topic Name")
    return DELETE_TOPIC


async def received_delete_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    topic = update.message.text.strip()

    if delete_note(topic):
        await update.message.reply_text("✅ Note Deleted Successfully.")
    else:
        await update.message.reply_text("❌ Topic not found.")

    return ConversationHandler.END


# ==========================================
# SEARCH NOTE
# ==========================================

async def note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text(
        "📝 Enter Class / Subject / Topic"
    )

    return SEARCH_QUERY


async def received_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.message.text.strip()

    results = search_notes(query) or []

    if not results:
        await update.message.reply_text("❌ No notes found.")
        return ConversationHandler.END

    await update.message.reply_text(
        f"🔍 {len(results)} Notes Found\n\nSending..."
    )

    for note in results[:20]:

        _, student_class, subject, topic, file_id, file_type, file_name = note

        caption = (
            f"📚 Class: {student_class}\n"
            f"📖 Subject: {subject}\n"
            f"📝 Topic: {topic}"
        )

        if file_type == "document":
            await update.message.reply_document(
                document=file_id,
                caption=caption
            )

        elif file_type == "photo":
            await update.message.reply_photo(
                photo=file_id,
                caption=caption
            )

    return ConversationHandler.END


# ==========================================
# ALL NOTES
# ==========================================

async def allnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    notes = get_all_notes() or []

    if not notes:
        await update.message.reply_text("❌ No notes available.")
        return

    text = "📚 Available Notes\n\n"

    for i, note in enumerate(notes, start=1):
        _, student_class, subject, topic, _, _, _ = note

        text += (
            f"{i}.\n"
            f"📚 {student_class}\n"
            f"📖 {subject}\n"
            f"📝 {topic}\n\n"
        )

    if len(text) > 4000:
        text = text[:3900] + "\n..."

    await update.message.reply_text(text)

# ==========================================
# EDIT NOTE
# ==========================================

async def editnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text("📝 Enter Existing Topic")

    return EDIT_OLD_TOPIC


async def received_old_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    old_topic = update.message.text.strip()

    notes = search_notes(old_topic) or []

    if not notes:
        await update.message.reply_text("❌ Topic not found.")
        return ConversationHandler.END

    context.user_data["old_topic"] = old_topic

    await update.message.reply_text("📚 Enter New Class")

    return EDIT_NEW_CLASS


async def received_new_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data["new_class"] = update.message.text.strip()

    await update.message.reply_text("📖 Enter New Subject")

    return EDIT_NEW_SUBJECT


async def received_new_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data["new_subject"] = update.message.text.strip()

    await update.message.reply_text("📝 Enter New Topic")

    return EDIT_NEW_TOPIC


async def received_new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    success = update_note(
        context.user_data["old_topic"],
        context.user_data["new_class"],
        context.user_data["new_subject"],
        update.message.text.strip(),
    )

    if success:
        await update.message.reply_text("✅ Note Updated Successfully.")
    else:
        await update.message.reply_text("❌ Update Failed.")

    context.user_data.clear()

    return ConversationHandler.END


# ==========================================
# CONVERSATION HANDLERS
# ==========================================

add_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("addnote", addnote_start)],
    states={
        CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_class)],
        SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_subject)],
        TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_topic)],
        FILE: [
            MessageHandler(
                filters.Document.ALL | filters.PHOTO,
                received_file,
            )
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

delete_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("deletenote", deletenote_start)],
    states={
        DELETE_TOPIC: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_delete_topic)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("note", note_start)],
    states={
        SEARCH_QUERY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_search_query)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

edit_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("editnote", editnote_start)],
    states={
        EDIT_OLD_TOPIC: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_topic)
        ],
        EDIT_NEW_CLASS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_class)
        ],
        EDIT_NEW_SUBJECT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_subject)
        ],
        EDIT_NEW_TOPIC: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_topic)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
   
