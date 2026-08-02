# ==========================================
# SAFE STATES (Conflict-free large integers)
# ==========================================
SEARCH_QUERY = 100
EDIT_OLD_TOPIC = 101
EDIT_NEW_CLASS = 102
EDIT_NEW_SUBJECT = 103
EDIT_NEW_TOPIC = 104


# ==========================================
# NEW FEATURE 1: Student Search Notes (/note)
# ==========================================

async def note_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /note conversation."""
    await update.message.reply_text("📝 Enter Class / Subject / Topic")
    return SEARCH_QUERY

async def received_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives query, searches database safely, and sends up to 20 matching files with strict file_type filtering."""
    query_text = update.message.text.strip()
    results = search_notes(query_text) or []  # None safety

    if not results:
        await update.message.reply_text("❌ No notes found.")
    else:
        total_notes = len(results)
        await update.message.reply_text(f"🔍 {total_notes} Notes Found\n\nSending...")

        for note in results[:20]:
            _, student_class, subject, topic, file_id, file_type, file_name = note
            caption = (
                f"📚 Class: {student_class}\n"
                f"📖 Subject: {subject}\n"
                f"📝 Topic: {topic}"
            )

            if file_type == "document":
                await update.message.reply_document(document=file_id, caption=caption)
            elif file_type == "photo":
                await update.message.reply_photo(photo=file_id, caption=caption)
            else:
                continue

    return ConversationHandler.END


# ==========================================
# NEW FEATURE 2: All Notes List (/allnotes)
# ==========================================

async def allnotes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command handler for /allnotes to list available notes with character length check."""
    notes = get_all_notes() or []

    if not notes:
        await update.message.reply_text("❌ No notes available.")
    else:
        response_lines = ["📚 Available Notes\n"]
        for index, note in enumerate(notes, start=1):
            _, student_class, subject, topic, _, _, _ = note
            response_lines.append(
                f"{index}.\n"
                f"📚 Class: {student_class}\n"
                f"📖 Subject: {subject}\n"
                f"📝 Topic: {topic}\n"
            )
        
        response = "\n".join(response_lines)
        
        # Telegram 4096 character limit protection cutoff
        if len(response) > 4000:
            response = response[:3900] + "\n\n..."
            
        await update.message.reply_text(response)


# ==========================================
# NEW FEATURE 3: Edit Note (/editnote - Admin Only)
# ==========================================

async def editnote_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /editnote conversation with admin verification."""
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text("📝 Enter Existing Topic")
    return EDIT_OLD_TOPIC

async def received_old_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validates existence of existing topic in database."""
    old_topic = update.message.text.strip()
    notes = search_notes(old_topic) or []
    matching_note = next((n for n in notes if n[3].lower() == old_topic.lower()), None)

    if not matching_note:
        await update.message.reply_text("❌ Topic not found.")
        return ConversationHandler.END

    context.user_data["edit_old_topic"] = matching_note[3]
    await update.message.reply_text("📚 Enter New Class")
    return EDIT_NEW_CLASS

async def received_new_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores new class and prompts for new subject."""
    context.user_data["edit_new_class"] = update.message.text.strip()
    await update.message.reply_text("📖 Enter New Subject")
    return EDIT_NEW_SUBJECT

async def received_new_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores new subject and prompts for new topic."""
    context.user_data["edit_new_subject"] = update.message.text.strip()
    await update.message.reply_text("📝 Enter New Topic")
    return EDIT_NEW_TOPIC

async def received_new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finalizes data updates via update_note()."""
    new_topic = update.message.text.strip()
    old_topic = context.user_data.get("edit_old_topic")
    new_class = context.user_data.get("edit_new_class")
    new_subject = context.user_data.get("edit_new_subject")

    success = update_note(old_topic, new_class, new_subject, new_topic)

    if success:
        await update.message.reply_text("✅ Note Updated Successfully.")
    else:
        await update.message.reply_text("❌ Update Failed.")

    context.user_data.clear()
    return ConversationHandler.END


# ==========================================
# NEW CONVERSATION HANDLER INSTANCES
# ==========================================

note_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("note", note_start)],
    states={
        SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_search_query)],
    },
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
