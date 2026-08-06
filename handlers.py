import html
import logging
import re
from functools import partial
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from database import (
    search_resources_smart,
    get_distinct_subjects,
    get_chapters_for_subject,
    get_files_for_chapter,
    increment_user_warning,
    add_or_update_user,
    increment_download_count,
    add_request,
    get_all_users,
)
from admin import (
    add_resource_cmd, 
    delete_resource_cmd, 
    edit_resource_cmd, 
    stats_cmd, 
    requests_cmd,
    backup_cmd,
    restore_cmd,
    is_admin
)

logger = logging.getLogger(__name__)

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def send_auto_deleting_files(update: Update, context: ContextTypes.DEFAULT_TYPE, files):
    if not files:
        return

    chat_id = update.effective_chat.id
    
    for file in files:
        try:
            file_type = str(file.get("file_type", "")).lower()
            file_name = str(file.get("file_name", "")).lower()

            is_photo = (
                "image" in file_type
                or "photo" in file_type
                or file_name.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
            )
            
            # Safe HTML Escaping
            subject = html.escape(str(file.get("subject", "")))
            chapter_num = html.escape(str(file.get("chapter_number", "")))
            chapter_name = html.escape(str(file.get("chapter_name", "")))
            
            caption = (
                f"📂 <b>{subject}</b> - Chapter {chapter_num}: {chapter_name}\n"
                "<i>(This file will automatically delete in 5 minutes)</i>"
            )
            
            # 1. Send file first
            if is_photo:
                sent_msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=file["file_id"],
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                sent_msg = await context.bot.send_document(
                    chat_id=chat_id,
                    document=file["file_id"],
                    caption=caption,
                    parse_mode="HTML"
                )
                
            # 2. Increment download count on successful delivery
            increment_download_count(file["id"])

            # 3. Schedule auto-deletion
            context.job_queue.run_once(
                delete_message_job,
                300,
                data={"chat_id": chat_id, "message_id": sent_msg.message_id}
            )

        except Exception as e:
            logger.error(f"Failed to send file ID {file.get('id')}: {e}")
            continue

async def track_user_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        add_or_update_user(user.id, user.username, user.first_name)

# --- Command Handlers ---

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await track_user_middleware(update, context)
    await update.message.reply_text(
        "👋 Welcome to the Ultimate Study Bot!\n\n"
        "You can search for notes, papers, formulasheets, chiragbooks, and shortnotes naturally by typing queries like:\n"
        "• `Physics notes`\n"
        "• `Math Chapter 2`\n"
        "• `Chemistry Chapter 5`\n\n"
        "Use /help to see all available commands.",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Available Commands:**\n\n"
        "**Student Commands:**\n"
        "• /note - Browse Notes\n"
        "• /shortnote - Browse Short Notes\n"
        "• /chiragbook - Browse Chirag Books\n"
        "• /formulasheet - Browse Formula Sheets\n"
        "• /papers - Browse Question Papers\n"
        "• /allnotes - View all resource archives\n"
        "• /help - Display this help message\n\n"
        "**Admin Commands:**\n"
        "• /addnote, /addshortnote, /addchiragbook, /addformulasheet, /addpaper\n"
        "• /broadcast - Send broadcast message to all users\n"
        "• /stats - Check bot metrics & downloads\n"
        "• /requests [limit] - View pending student material requests\n"
        "• /backup - Download database backup\n"
        "• /restore - Restore database from backup file",
        parse_mode="Markdown"
    )

async def myid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"👤 Your Telegram ID: `{user.id}`", parse_mode="Markdown")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to the message you want to broadcast.")
        return

    users = get_all_users()
    success = 0
    fail = 0
    broadcast_msg = update.message.reply_to_message

    for uid in users:
        try:
            await broadcast_msg.copy(chat_id=uid)
            success += 1
        except Exception:
            fail += 1

    await update.message.reply_text(f"📢 Broadcast completed!\n✅ Success: {success}\n❌ Failed: {fail}")

async def category_browse_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = "notes"):
    await track_user_middleware(update, context)
    subjects = get_distinct_subjects(category)
    if not subjects:
        await update.message.reply_text(f"📂 No records found for category: **{category}**.", parse_mode="Markdown")
        return
        
    keyboard = [[InlineKeyboardButton(sub, callback_data=f"sub_{category}_{sub}")] for sub in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"📚 Select a subject for **{category.upper()}**:", reply_markup=reply_markup, parse_mode="Markdown")

async def all_notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await category_browse_cmd(update, context, "notes")

# --- Chat Member Welcomes & Goodbyes ---

async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return
    new_status = result.new_chat_member.status
    old_status = result.old_chat_member.status
    user = result.new_chat_member.user

    if old_status in ["left", "kicked"] and new_status == "member":
        add_or_update_user(user.id, user.username, user.first_name)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Welcome to the group, {user.first_name}! 🎉 Feel free to look up any study resources."
        )
    elif old_status in ["member", "administrator"] and new_status in ["left", "kicked"]:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Goodbye {user.first_name}! Hope to see you back soon. 👋"
        )

# --- Anti-Link & Warning System ---

async def anti_link_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text
    tg_link_pattern = re.compile(
        r"(https?://)?(www\.)?(t\.me|telegram\.me|telegram\.dog)/",
        re.IGNORECASE,
    )
    
    if tg_link_pattern.search(text):
        try:
            await update.message.delete()
        except Exception:
            pass
            
        user = update.effective_user
        warns = increment_user_warning(user.id)
        
        warning_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ <a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>, Telegram links are strictly prohibited in this group!\n⚠️ Warning Count: {warns}",
            parse_mode="HTML"
        )
        context.job_queue.run_once(delete_message_job, 30, data={"chat_id": update.effective_chat.id, "message_id": warning_msg.message_id})

# --- Smart Search & Group Interaction ---

async def smart_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    tg_link_pattern = re.compile(r"(https?://)?(www\.)?(t\.me|telegram\.me|telegram\.dog)/", re.IGNORECASE)
    if tg_link_pattern.search(text):
        return  # Ignore deleted link messages

    await track_user_middleware(update, context)
    chat_type = update.effective_chat.type
    results = search_resources_smart(text)
    
    if results:
        sent_chapters = set()
        for res in results:
            key = (res["category"], res["subject"], res["chapter_number"])
            if key not in sent_chapters:
                sent_chapters.add(key)
                chapter_files = get_files_for_chapter(res["category"], res["subject"], res["chapter_number"])
                await send_auto_deleting_files(update, context, chapter_files)
    else:
        keywords = ["note", "notes", "pdf", "chapter", "class", "sheet", "book"]
        if any(k in text.lower() for k in keywords):
            add_request(update.effective_user.id, "notes", text, 1)
            if chat_type in ["group", "supergroup"]:
                await update.message.reply_text("Which notes do you need? Your request has been logged for admin review.")
            else:
                await update.message.reply_text("❌ Resource not found. Your request has been sent to our admin team!")

# --- Inline Query Callbacks ---

async def inline_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("sub_"):
        _, category, subject = data.split("_", 2)
        chapters = get_chapters_for_subject(category, subject)
        keyboard = [
            [InlineKeyboardButton(f"Chapter {ch['chapter_number']}: {ch['chapter_name']}", callback_data=f"chap_{category}_{subject}_{ch['chapter_number']}")]
            for ch in chapters
        ]
        keyboard.append([InlineKeyboardButton("🔙 Back to Subjects", callback_data=f"backcat_{category}")])
        await query.edit_message_text(text=f"📖 Chapters for **{subject}** ({category.upper()}):", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("chap_"):
        _, category, subject, ch_num_str = data.split("_", 3)
        ch_num = int(ch_num_str)
        files = get_files_for_chapter(category, subject, ch_num)
        
        try:
            await query.message.delete()
        except Exception:
            pass

        await send_auto_deleting_files(update, context, files)

    elif data.startswith("backcat_"):
        _, category = data.split("_", 1)
        subjects = get_distinct_subjects(category)
        keyboard = [[InlineKeyboardButton(sub, callback_data=f"sub_{category}_{sub}")] for sub in subjects]
        await query.edit_message_text(text=f"📚 Select a subject for **{category.upper()}**:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- Register Handlers ---

def register_handlers(application: Application):
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("myid", myid_cmd))
    application.add_handler(CommandHandler("allnotes", all_notes_cmd))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("requests", requests_cmd))
    application.add_handler(CommandHandler("backup", backup_cmd))
    application.add_handler(CommandHandler("restore", restore_cmd))
    
    # Category browse commands
    application.add_handler(CommandHandler("note", partial(category_browse_cmd, category="notes")))
    application.add_handler(CommandHandler("shortnote", partial(category_browse_cmd, category="shortnote")))
    application.add_handler(CommandHandler("chiragbook", partial(category_browse_cmd, category="chiragbook")))
    application.add_handler(CommandHandler("formulasheet", partial(category_browse_cmd, category="formulasheet")))
    application.add_handler(CommandHandler("papers", partial(category_browse_cmd, category="papers")))

    # Admin add resource commands
    application.add_handler(CommandHandler("addnote", partial(add_resource_cmd, category="notes")))
    application.add_handler(CommandHandler("addshortnote", partial(add_resource_cmd, category="shortnote")))
    application.add_handler(CommandHandler("addchiragbook", partial(add_resource_cmd, category="chiragbook")))
    application.add_handler(CommandHandler("addformulasheet", partial(add_resource_cmd, category="formulasheet")))
    application.add_handler(CommandHandler("addpaper", partial(add_resource_cmd, category="papers")))

    # Admin edit command wrappers
    categories_map = [
        ("note", "notes"), 
        ("shortnote", "shortnote"), 
        ("chiragbook", "chiragbook"), 
        ("formulasheet", "formulasheet"), 
        ("paper", "papers")
    ]
    for prefix, cat_name in categories_map:
        del_cmd = "deletenote" if prefix == "note" else f"delete{prefix}"
        edit_cmd = f"edit{prefix}"
        application.add_handler(CommandHandler(del_cmd, delete_resource_cmd))
        application.add_handler(CommandHandler(edit_cmd, partial(edit_resource_cmd, category=cat_name)))

    application.add_handler(ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER))

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), anti_link_filter), group=0)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), smart_text_handler), group=1)

    application.add_handler(CallbackQueryHandler(inline_button_callback))
