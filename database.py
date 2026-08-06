import sqlite3

DB_NAME = "bot_data.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                warnings INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Resources table (Standardized column: download_count)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                subject TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                chapter_name TEXT NOT NULL,
                student_class TEXT,
                file_id TEXT NOT NULL,
                file_type TEXT,
                file_name TEXT,
                download_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                query_text TEXT,
                status INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    finally:
        conn.close()

# --- User Functions ---

def add_or_update_user(user_id, username, first_name):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
        conn.commit()
    finally:
        conn.close()

def increment_user_warning(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Atomic upsert warning count
        cursor.execute("""
            INSERT INTO users (user_id, warnings)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                warnings = warnings + 1
        """, (user_id,))
        
        cursor.execute("SELECT warnings FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.commit()
        return row["warnings"] if row else 1
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()
        return [r["user_id"] for r in rows]
    finally:
        conn.close()

# --- Resource Functions ---

def add_resource(category, subject, chapter_number, chapter_name, student_class, file_id, file_type=None, file_name=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resources (category, subject, chapter_number, chapter_name, student_class, file_id, file_type, file_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (category, subject, chapter_number, chapter_name, student_class, file_id, file_type, file_name))
        resource_id = cursor.lastrowid
        conn.commit()
        return resource_id
    finally:
        conn.close()

def soft_delete_resource(resource_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE resources SET is_active = 0 WHERE id = ?", (resource_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def increment_download_count(resource_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE resources SET download_count = download_count + 1 WHERE id = ?", (resource_id,))
        conn.commit()
    finally:
        conn.close()

def search_resources_smart(text):
    text = text.strip()
    if not text:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = f"%{text}%"
        
        cursor.execute("""
            SELECT * FROM resources 
            WHERE is_active = 1 AND (
                subject LIKE ? 
                OR chapter_name LIKE ? 
                OR student_class LIKE ? 
                OR category LIKE ?
                OR CAST(chapter_number AS TEXT) LIKE ?
            )
        """, (query, query, query, query, query))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_distinct_subjects(category):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT subject FROM resources 
            WHERE category = ? AND is_active = 1 
            ORDER BY subject ASC
        """, (category,))
        rows = cursor.fetchall()
        return [row["subject"] for row in rows]
    finally:
        conn.close()

def get_chapters_for_subject(category, subject):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT chapter_number, chapter_name FROM resources 
            WHERE category = ? AND subject = ? AND is_active = 1 
            ORDER BY chapter_number ASC
        """, (category, subject))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_files_for_chapter(category, subject, chapter_number):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM resources 
            WHERE category = ? AND subject = ? AND chapter_number = ? AND is_active = 1
        """, (category, subject, chapter_number))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

# --- Requests Functions ---

def add_request(user_id, category, query_text, status=1):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO requests (user_id, category, query_text, status)
            VALUES (?, ?, ?, ?)
        """, (user_id, category, query_text, status))
        conn.commit()
    finally:
        conn.close()
