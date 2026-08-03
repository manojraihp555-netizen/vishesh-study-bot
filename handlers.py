import os
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
import sqlite3
from openai import OpenAI

from database import (
    add_note,
    delete_note,
    search_notes,
    get_all_notes,
    update_note,
    add_user,
    get_all_users,
)
from admin import is_admin

# सुरक्षित तरीके से एनवायरनमेंट से OpenAI API Key लोड करें
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

CLASS = 0
SUBJECT = 1
TOPIC = 2
FILE = 3
DELETE_TOPIC = 4
SEARCH_QUERY = 100
EDIT_OLD_TOPIC = 101
EDIT_NEW_CLASS = 102
EDIT_NEW_SUBJECT = 103
EDIT_NEW_TOPIC = 104

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    await update.message.reply_text(
        "👋 Welcome to Vishesh Study Bot!\n\n"
        "📚 Use /help to see all commands.\n"
        "🤖 You can also ask me any study question directly in chat!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Available Commands\n\n"
        "/start - Start bot\n"
        "/help - Show commands\n"
        "/myid - Get your Telegram ID\n"
        "/note - Search notes\n"
        "/allnotes - View subject-wise notes\n\n"
        "Admin Commands:\n"
        "/broadcast - Send notice to all users\n"
        "/addnote - Add a new note\n"
        "/deletenote - Delete a note\n"
        "/editnote - Edit a note"
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your Telegram ID:\n{update.effective_user.id}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# DIRECT CHATGPT MESSAGE HANDLER
async def handle_direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("in_conversation"):
        return

    user_question = update.message.text.strip()
    if user_question.startswith("/"):
        return

    if not ai_client:
        await update.message.reply_text("❌ OpenAI API Key is not configured properly in server variables.")
        return

    await update.message.reply_chat_action("typing")

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_question}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"❌ माफ कीजिए, जवाब देने में समस्या आई: {e}")

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    message_text = " ".join(context.args)
    if not message_text and not update.message.reply_to_message:
        await update.message.reply_text("❌ कृपया नोटिस लिखें। उदाहरण:\n`/broadcast 📢 Notice`", parse_mode="Markdown")
        return

    target_message = update.message.reply_to_message if update.message.reply_to_message else update.message
    user_ids = get_all_users()
    
    if not user_ids:
        await update.message.reply_text("❌ No users found.")
        return

    sent_count = 0
    failed_count = 0
    status_msg = await update.message.reply_text(f"🚀 Broadcasting message to {len(user_ids)} users...")

    for uid in user_ids:
        try:
            if update.message.reply_to_message:
                await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=target_message.message_id)
            else:
                await context.bot.send_message(chat_id=uid, text=message_text)
            sent_count += 1
        except Exception:
            failed_count += 1

    await status_msg.edit_text(f"✅ Broadcast Completed!\n📤 Sent: {sent_count}\n❌ Failed: {failed_count}")

async def addnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END
    context.user_data.clear()
    context.user_data["in_conversation"] = True
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
    await update.message.reply_text("📎 Send PDF or Photo")
    return FILE

async def received_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    file_id = None
    file_type = None
    file_name = ""

    if update.message.document and update.message.document.mime_type == "application/pdf":
        file_id = update.message.document.file_id
        file_type = "document"
        file_name = update.message.document.file_name or "document.pdf"
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        file_name = "Photo"
    else:
        await update.message.reply_text("❌ Please send only PDF or Photo.")
        return FILE

    add_note(context.user_data["class"], context.user_data["subject"], context.user_data["topic"], file_id, file_type, file_name)
    await update.message.reply_text("✅ Note Added Successfully.")
    context.user_data.clear()
    return ConversationHandler.END

async def deletenote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END
    context.user_data["in_conversation"] = True
    await update.message.reply_text("🗑 Enter Topic Name")
    return DELETE_TOPIC

async def received_delete_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if delete_note(update.message.text.strip()):
        await update.message.reply_text("✅ Note Deleted Successfully.")
    else:
        await update.message.reply_text("❌ Topic not found.")
    context.user_data.clear()
    return ConversationHandler.END

async def note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["in_conversation"] = True
    await update.message.reply_text("📝 Enter Class / Subject / Topic")
    return SEARCH_QUERY

async def received_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    results = search_notes(update.message.text.strip()) or []
    if not results:
        await update.message.reply_text("❌ No notes found.")
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text(f"🔍 {len(results)} Notes Found.")
    for note in results[:20]:
        try:
            student_class, subject, topic, file_id, file_type = note["student_class"], note["subject"], note["topic"], note["file_id"], note["file_type"]
            caption = f"📚 Class: {student_class}\n📖 Subject: {subject}\n📝 Topic: {topic}"
            if file_type == "document":
                await update.message.reply_document(document=file_id, caption=caption)
            elif file_type == "photo":
                await update.message.reply_photo(photo=file_id, caption=caption)
        except Exception:
            pass

    context.user_data.clear()
    return ConversationHandler.END

async def allnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes = get_all_notes() or []
    if not notes:
        await update.message.reply_text("❌ No notes available.")
        return

    grouped_notes = {}
    for note in notes:
        sub_key = note["subject"].strip().title()
        if sub_key not in grouped_notes:
            grouped_notes[sub_key] = []
        grouped_notes[sub_key].append((note["student_class"], note["topic"]))

    text = "📚 **Available Notes (Subject-wise)**\n"
    for subject, items in sorted(grouped_notes.items()):
        text += f"\n📖 **Subject: {subject}**\n"
        for idx, (cls, topic) in enumerate(items, start=1):
            text += f"   {idx}. Class: {cls} | Topic: {topic}\n"

    if len(text) > 4000:
        text = text[:3900] + "\n..."

    await update.message.reply_text(text, parse_mode="Markdown")

async def editnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END
    context.user_data.clear()
    context.user_data["in_conversation"] = True
    await update.message.reply_text("📝 Enter Existing Topic")
    return EDIT_OLD_TOPIC

async def received_old_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    old_topic = update.message.text.strip()
    notes = search_notes(old_topic) or []
    matching = next((n["topic"] for n in notes if n["topic"].lower() == old_topic.lower()), None)

    if not matching:
        await update.message.reply_text("❌ Topic not found.")
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["old_topic"] = matching
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
    success = update_note(context.user_data["old_topic"], context.user_data["new_class"], context.user_data["new_subject"], update.message.text.strip())
    if success:
        await update.message.reply_text("✅ Note Updated Successfully.")
    else:
        await update.message.reply_text("❌ Update Failed.")
    context.user_data.clear()
    return ConversationHandler.END

add_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("addnote", addnote_start)],
    states={
        CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_class)],
        SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_subject)],
        TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_topic)],
        FILE: [MessageHandler((filters.Document.PDF | filters.PHOTO | filters.TEXT) & ~filters.COMMAND, received_file)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

delete_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("deletenote", deletenote_start)],
    states={DELETE_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_delete_topic)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("note", note_start)],
    states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_search_query)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

edit_note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("editnote", editnote_start)],
    states={
        EDIT_OLD_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_old_topic)],
        EDIT_NEW_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_class)],
        EDIT_NEW_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_subject)],
        EDIT_NEW_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_topic)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
