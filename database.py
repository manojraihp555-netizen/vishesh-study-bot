def search_resources_smart(text):
    text = text.strip()
    if not text:
        return []

    conn = get_connection()
    cursor = conn.cursor()
    query = f"%{text}%"
    
    cursor.execute(
        """
        SELECT * FROM resources 
        WHERE is_active = 1 AND (
            subject LIKE ? 
            OR chapter_name LIKE ? 
            OR student_class LIKE ? 
            OR category LIKE ?
            OR CAST(chapter_number AS TEXT) LIKE ?
        )
        """,
        (query, query, query, query, query)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
