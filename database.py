import sqlite3
import logging
from config import DB_FILE

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
    conn.row_factory = sqlite3.Row
    return conn


def add_note(student_class, subject, topic, file_id, file_type, file_name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO notes
            (student_class, subject, topic, file_id, file_type, file_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_class,
            subject,
            topic.strip(),
            file_id,
            file_type,
            file_name
        ))

        conn.commit()
        logger.info(f"Note added: {topic}")

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
                LOWER(TRIM(topic)) LIKE LOWER(TRIM(?))
                OR LOWER(TRIM(subject)) LIKE LOWER(TRIM(?))
                OR LOWER(TRIM(student_class)) LIKE LOWER(TRIM(?))
            ORDER BY student_class, subject, topic
        """, (
            f"%{query}%",
            f"%{query}%",
            f"%{query}%"
        ))

        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database Error in search_notes: {e}")
        return []

    finally:
        conn.close()


def delete_note(topic):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        logger.info(f"Trying to delete topic: {topic}")

        cursor.execute("""
            DELETE FROM notes
            WHERE LOWER(TRIM(topic)) = LOWER(TRIM(?))
        """, (topic,))

        conn.commit()

        logger.info(f"Rows deleted: {cursor.rowcount}")

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
            ORDER BY student_class, subject, topic
        """)

        return cursor.fetchall()

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
            SET
                student_class=?,
                subject=?,
                topic=?
            WHERE LOWER(TRIM(topic)) = LOWER(TRIM(?))
        """, (
            new_class.strip(),
            new_subject.strip(),
            new_topic.strip(),
            old_topic.strip()
        ))

        conn.commit()

        logger.info(f"Rows updated: {cursor.rowcount}")

        return cursor.rowcount > 0

    except sqlite3.Error as e:
        logger.error(f"Database Error in update_note: {e}")
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
