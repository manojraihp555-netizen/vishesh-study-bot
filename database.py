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
