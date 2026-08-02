import sqlite3
import logging
from config import DB_FILE

logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Notes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_class TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Users Table (For Broadcast)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def add_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database Error in add_user: {e}")
    finally:
        conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users")
        results = cursor.fetchall()
        user_ids = [row["user_id"] if isinstance(row, sqlite3.Row) else row[0] for row in results]
        return user_ids
    except sqlite3.Error as e:
        logger.error(f"Database Error in get_all_users: {e}")
        return []
    finally:
        conn.close()


def add_note(student_class, subject, topic, file_id, file_type, file_name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO notes
            (student_class, subject, topic, file_id, file_type, file_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_class.strip().title(),
            subject.strip().title(),
            topic.strip(),
            file_id,
            file_type,
            file_name
        ))

        conn.commit()
        logger.info(f"Note added successfully: {subject} - {topic}")

    except sqlite3.Error as e:
        logger.error(f"Database Error in add_note: {e}")

    finally:
        conn.close()


def search_notes(query):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                student_class,
                subject,
                topic,
                file_id,
                file_type,
                file_name
            FROM notes
            WHERE
                LOWER(topic) LIKE LOWER(?)
                OR LOWER(subject) LIKE LOWER(?)
                OR LOWER(student_class) LIKE LOWER(?)
        """, (
            f"%{query}%",
            f"%{query}%",
            f"%{query}%"
        ))

        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        logger.error(f"Database Error in search_notes: {e}")
        return []

    finally:
        conn.close()


def delete_note(topic):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM notes
            WHERE LOWER(topic) = LOWER(?)
        """, (topic,))

        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        logger.error(f"Database Error in delete_note: {e}")
        return False

    finally:
        conn.close()


def get_all_notes():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                student_class,
                subject,
                topic,
                file_id,
                file_type,
                file_name
            FROM notes
            ORDER BY student_class ASC, subject ASC, topic ASC
        """)
        results = cursor.fetchall()
        return results

    except sqlite3.Error as e:
        logger.error(f"Database Error in get_all_notes: {e}")
        return []

    finally:
        conn.close()


def update_note(old_topic, new_class, new_subject, new_topic):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE notes
            SET student_class = ?, subject = ?, topic = ?
            WHERE LOWER(topic) = LOWER(?)
        """, (new_class.strip().title(), new_subject.strip().title(), new_topic.strip(), old_topic))

        conn.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        logger.error(f"Database Error in update_note: {e}")
        return False

    finally:
        conn.close()
