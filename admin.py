import sqlite3
import os
import shutil
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

DB_NAME = "bot_data.db"
ADMIN_IDS = [123456789]  # Replace with actual admin Telegram user IDs

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_connection():
    """
    Database connection helper with row_factory enabled 
    for dict-like column access.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- Helper Query Functions ---

def soft_delete_resource(target):
    """
    Soft deletes a resource by setting is_active = 0.
    Accepts integer ID or chapter name string.
    Returns True if record was updated, False otherwise.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if str(target).isdigit():
            cursor.execute(
                "UPDATE resources SET is_active = 0 WHERE id = ?",
                (int(target),)
            )
        else:
            cursor.execute(
                "UPDATE resources SET is_active = 0 WHERE LOWER(chapter_name) = ?",
                (str(target).strip().lower(),)
            )

        affected_rows = cursor.rowcount
        conn.commit()
        return affected_rows > 0

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_top_downloads_active(limit=5):
    """
    Fetches top active resources based on download count.
    Uses standardized column name 'download_count'.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM resources
            WHERE is_active = 1
            ORDER BY download_count DESC
            LIMIT ?
        """, (limit,))

        return cursor.fetchall()

    finally:
        conn.close()

def get_category_counts_active():
    """
    Returns a dictionary mapping category names to total active resource count.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT category, COUNT(*) AS cnt
            FROM resources
            WHERE is_active = 1
            GROUP BY category
        """)

        return {
            row["category"]: row["cnt"]
            for row in cursor.fetchall()
        }

    finally:
        conn.close()

# --- Admin Command Handlers ---

async def add_resource_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = "notes"):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    await update.message.reply_text(
        f"➕ Send or reply with the file/details to add a new resource under category: <b>{category.upper()}</b>",
        parse_mode="HTML"
    )

async def delete_resource_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /deletenote <resource_id or chapter_name>")
        return

    target = " ".join(context.args)
    if soft_delete_resource(target):
        await update.message.reply_text(f"✅ Resource <b>'{target}'</b> deactivated successfully.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ Could not find or deactivate resource: <b>'{target}'</b>.", parse_mode="HTML")

async def edit_resource_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = "notes"):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    await update.message.reply_text(f"✏️ Editing tools for category <b>{category.upper()}</b>.", parse_mode="HTML")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    counts = get_category_counts_active()
    top_downloads = get_top_downloads_active(limit=5)

    stats_text = "📊 <b>Bot Active Metrics</b>\n\n"
    stats_text += "<b>Category Breakdown:</b>\n"
    if counts:
        for cat, cnt in counts.items():
            stats_text += f"• {cat.capitalize()}: {cnt}\n"
    else:
        stats_text += "• No active resources available.\n"

    stats_text += "\n🔥 <b>Top Downloaded Resources:</b>\n"
    if top_downloads:
        for row in top_downloads:
            stats_text += f"• {row['subject']} (Ch {row['chapter_number']}): <b>{row['download_count']}</b> downloads\n"
    else:
        stats_text += "• No downloads recorded yet.\n"

    await update.message.reply_text(stats_text, parse_mode="HTML")

async def requests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    limit = 5
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE status = 1 ORDER BY id DESC LIMIT ?", (limit,))
        reqs = cursor.fetchall()
        
        if not reqs:
            await update.message.reply_text("🎉 No pending resource requests!")
            return

        msg = "📝 <b>Pending Student Requests:</b>\n\n"
        for r in reqs:
            msg += f"• ID {r['id']} | User {r['user_id']}: <i>{r['query_text']}</i>\n"
        
        await update.message.reply_text(msg, parse_mode="HTML")
    finally:
        conn.close()

async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    if os.path.exists(DB_NAME):
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(DB_NAME, "rb"),
            caption="📦 Database Backup Document"
        )
    else:
        await update.message.reply_text("❌ Database file not found.")

async def restore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ Reply to a database `.db` file with `/restore` to restore.")
        return

    doc = update.message.reply_to_message.document
    if not doc.file_name.endswith(".db"):
        await update.message.reply_text("❌ Invalid file format! Must be a `.db` SQLite file.")
        return

    file = await context.bot.get_file(doc.file_id)
    backup_path = f"{DB_NAME}.bak"
    
    if os.path.exists(DB_NAME):
        shutil.copyfile(DB_NAME, backup_path)

    await file.download_to_drive(DB_NAME)
    await update.message.reply_text("✅ Database restored successfully! Safety backup created.")
