import sqlite3

DB_NAME = "bot_data.db"

def get_connection():
    """
    Database connection helper with row_factory enabled 
    for dict-like column access.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


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
