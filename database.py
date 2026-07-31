import sqlite3
import logging
from config import DB_FILE

# Sirf logger instance, basicConfig yahan nahi rahega
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_class TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_class, subject, topic, file_id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Future-proof aur clean access ke liye
    return conn

def add_note(student_class, subject, topic, file_id, file_type, file_name):
    """Database mein naya note add karne ke liye"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO notes (student_class, subject, topic, file_id, file_type, file_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_class, subject, topic, file_id, file_type, file_name))
        conn.commit()
        logger.info(f"Note added successfully: {subject} - {topic}")
    except sqlite3.Error as e:
        logger.error(f"Database Error in add_note: {e}")
    finally:
        conn.close()

def search_notes(query):
    """Case-insensitive smart search ke liye"""
    conn = get_connection()
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute("""
            SELECT student_class, subject, topic, file_id, file_type, file_name 
            FROM notes 
            WHERE LOWER(topic) LIKE LOWER(?) 
               OR LOWER(subject) LIKE LOWER(?) 
               OR LOWER(student_class) LIKE LOWER(?)
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        results = cursor.fetchall()
        logger.info(f"Search performed for query: '{query}', found {len(results)} results.")
    except sqlite3.Error as e:
        logger.error(f"Database Error in search_notes: {e}")
    finally:
        conn.close()
    return results

if __name__ == "__main__":
    init_db()
