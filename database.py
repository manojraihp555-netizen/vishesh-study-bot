import sqlite3

def get_connection():
    conn = sqlite3.connect("bot_database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Resources table with all required columns including downloads and is_active
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            student_class TEXT,
            subject TEXT,
            chapter_number INTEGER,
            chapter_name TEXT,
            file_id TEXT,
            file_type TEXT,
            file_name TEXT,
            downloads INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Users tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            warnings INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0
        )
    """)
    
    # Material requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            query TEXT,
            status INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()

def add_note(student_class, subject, chapter_number, chapter_name, file_id, file_type, file_name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO resources (
                category,
                student_class,
                subject,
                chapter_number,
                chapter_name,
                file_id,
                file_type,
                file_name,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "notes",
                student_class.strip(),
                subject.strip().title(),
                int(chapter_number),
                chapter_name.strip(),
                file_id,
                file_type,
                file_name.strip(),
                1
            )
        )
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def search_resources_smart(text):
    conn = get_connection()
    cursor = conn.cursor()
    query = f"%{text}%"
    cursor.execute(
        "SELECT * FROM resources WHERE is_active = 1 AND (subject LIKE ? OR chapter_name LIKE ?)",
        (query, query)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_distinct_subjects(category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT subject FROM resources WHERE category = ? AND is_active = 1",
        (category,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row["subject"] for row in rows]

def get_chapters_for_subject(category, subject):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT chapter_number, chapter_name FROM resources WHERE category = ? AND subject = ? AND is_active = 1 ORDER BY chapter_number ASC",
        (category, subject)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_files_for_chapter(category, subject, chapter_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM resources WHERE category = ? AND subject = ? AND chapter_number = ? AND is_active = 1",
        (category, subject, chapter_number)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def increment_user_warning(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
    cursor.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["warnings"] if row else 1

def add_or_update_user(user_id, username, first_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username = excluded.username, first_name = excluded.first_name
        """,
        (user_id, username, first_name)
    )
    conn.commit()
    conn.close()

def increment_download_count(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE resources SET downloads = downloads + 1 WHERE id = ?",
        (resource_id,)
    )
    conn.commit()
    conn.close()

def add_request(user_id, category, query, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, category, query, status) VALUES (?, ?, ?, ?)",
        (user_id, category, query, status)
    )
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row["user_id"] for row in rows]

# --- Admin Required Functions ---

def soft_delete_resource(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE resources SET is_active = 0 WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()

def delete_note(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()

def update_note(resource_id, subject, chapter_number, chapter_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE resources 
        SET subject = ?, chapter_number = ?, chapter_name = ? 
        WHERE id = ?
        """,
        (subject.strip().title(), int(chapter_number), chapter_name.strip(), resource_id)
    )
    conn.commit()
    conn.close()

def get_top_downloads_active(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM resources WHERE is_active = 1 ORDER BY downloads DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_category_counts_active():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, COUNT(*) as count FROM resources WHERE is_active = 1 GROUP BY category"
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["category"]: row["count"] for row in rows}
