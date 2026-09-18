import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Movies jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT,
                file_id TEXT NOT NULL,
                caption TEXT,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Majburiy obuna kanallari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT,
                invite_link TEXT NOT NULL
            )
        """)
        
        await db.commit()


# ==================== FOYDALANUVCHILAR ====================

async def add_user(user_id: int, username: str | None, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ==================== KINOLAR ====================

async def add_movie(code: str, file_id: str, title: str = "", caption: str = "") -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO movies (code, file_id, title, caption) VALUES (?, ?, ?, ?)",
                (code.strip(), file_id, title, caption)
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def get_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Kod bo'yicha qidirish
        async with db.execute(
            "SELECT id, code, title, file_id, caption, views FROM movies WHERE code = ?",
            (code.strip(),)
        ) as cursor:
            movie = await cursor.fetchone()
            if movie:
                # Ko'rishlar sonini oshiramiz
                await db.execute("UPDATE movies SET views = views + 1 WHERE id = ?", (movie[0],))
                await db.commit()
                return {
                    "id": movie[0],
                    "code": movie[1],
                    "title": movie[2],
                    "file_id": movie[3],
                    "caption": movie[4],
                    "views": movie[5] + 1
                }
            return None


async def delete_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code.strip(),))
        await db.commit()
        return cursor.rowcount > 0


async def count_movies() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_recent_movies(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT code, title, views FROM movies ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()


# ==================== KANALLAR ====================

async def add_channel(channel_id: str, channel_name: str, invite_link: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO channels (channel_id, channel_name, invite_link) VALUES (?, ?, ?)",
                (channel_id.strip(), channel_name, invite_link.strip())
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, channel_id, channel_name, invite_link FROM channels") as cursor:
            return await cursor.fetchall()


async def delete_channel(channel_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id.strip(),))
        await db.commit()
        return cursor.rowcount > 0
