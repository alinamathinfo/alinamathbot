import aiosqlite

DB_NAME = "students.db"

async def init_db():
    """Создаёт таблицу, если её нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                name TEXT,
                subjects TEXT
            )
        """)
        await db.commit()

async def add_student(user_id: int, name: str):
    """Добавляет ученика без предметов"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO students (user_id, name, subjects) VALUES (?, ?, '')", (user_id, name))
        await db.commit()

async def update_subjects(user_id: int, new_subject: str):
    """Добавляет предмет ученику"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT subjects FROM students WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                existing_subjects = row[0].split(", ") if row[0] else []
                if new_subject not in existing_subjects:
                    existing_subjects.append(new_subject)
                    await db.execute("UPDATE students SET subjects = ? WHERE user_id = ?",
                                     (", ".join(existing_subjects), user_id))
                    await db.commit()
                    return existing_subjects
    return None

async def get_student(user_id: int):
    """Получает данные ученика"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT name, subjects FROM students WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()
