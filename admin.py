def soft_delete_resource(target):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if str(target).isdigit():
            cursor.execute("UPDATE resources SET is_active = 0 WHERE id = ?", (int(target),))
        else:
            cursor.execute("UPDATE resources SET is_active = 0 WHERE LOWER(chapter_name) = ?", (str(target).strip().lower(),))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_top_downloads_active(limit=5):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM resources 
            WHERE is_active = 1 
            ORDER BY download_count DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()

def get_category_counts_active():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) as cnt FROM resources WHERE is_active = 1 GROUP BY category")
        return {row["category"]: row["cnt"] for row in cursor.fetchall()}
    finally:
        conn.close()
