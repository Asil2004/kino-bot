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
                is_subscribed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        try:
            await db.execute("ALTER TABLE users ADD COLUMN is_subscribed INTEGER DEFAULT 0")
        except Exception:
            pass
        
        # Movies jadvali (Kino va Seriallar)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                movie_type TEXT DEFAULT 'single',
                year TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                language TEXT DEFAULT "O'zbek tilida",
                photo_id TEXT DEFAULT '',
                file_id TEXT DEFAULT '',
                caption TEXT DEFAULT '',
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Qo'shimcha ustunlarni tekshirish (mavjud bazalar uchun)
        columns_to_add = [
            ("movie_type", "TEXT DEFAULT 'single'"),
            ("year", "TEXT DEFAULT ''"),
            ("genre", "TEXT DEFAULT ''"),
            ("language", "TEXT DEFAULT 'O''zbek tilida'"),
            ("photo_id", "TEXT DEFAULT ''"),
        ]
        for col_name, col_type in columns_to_add:
            try:
                await db.execute(f"ALTER TABLE movies ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
        
        # Episodes jadvali (Serial va Anime qismlari)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_code TEXT NOT NULL,
                episode_number INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                title TEXT DEFAULT '',
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(movie_code, episode_number)
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


async def set_user_subscribed(user_id: int, status: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_subscribed = ? WHERE user_id = ?", (status, user_id))
        await db.commit()


async def is_user_sub_confirmed(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_subscribed FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row and row[0] == 1)


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


# ==================== KINOLAR VA SERIALLAR ====================

async def add_movie(
    code: str, file_id: str, title: str, 
    movie_type: str = "single", year: str = "", genre: str = "", 
    language: str = "O'zbek tilida", photo_id: str = "", caption: str = ""
) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO movies 
                (code, title, movie_type, year, genre, language, photo_id, file_id, caption) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code.strip(), title.strip(), movie_type, year, genre, language, photo_id, file_id, caption)
            )
            await db.commit()
            return True
    except Exception:
        return False


async def get_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT id, code, title, movie_type, year, genre, language, photo_id, file_id, caption, views 
            FROM movies WHERE code = ?
            """,
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
                    "movie_type": movie[3] or "single",
                    "year": movie[4] or "",
                    "genre": movie[5] or "",
                    "language": movie[6] or "O'zbek tilida",
                    "photo_id": movie[7] or "",
                    "file_id": movie[8] or "",
                    "caption": movie[9] or "",
                    "views": movie[10] + 1
                }
            return None


async def delete_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM episodes WHERE movie_code = ?", (code.strip(),))
        cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code.strip(),))
        await db.commit()
        return cursor.rowcount > 0


async def count_movies() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_recent_movies(limit: int = 15):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT code, title, movie_type, views FROM movies ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()


# ==================== QISMLAR (EPISODES) ====================

async def add_episode(movie_code: str, episode_number: int, file_id: str, title: str = "") -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO episodes (movie_code, episode_number, file_id, title)
                VALUES (?, ?, ?, ?)
                """,
                (movie_code.strip(), int(episode_number), file_id, title.strip())
            )
            await db.commit()
            return True
    except Exception:
        return False


async def get_episodes(movie_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT episode_number, title, views FROM episodes 
            WHERE movie_code = ? ORDER BY episode_number ASC
            """,
            (movie_code.strip(),)
        ) as cursor:
            return await cursor.fetchall()


async def get_episode(movie_code: str, episode_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT id, movie_code, episode_number, file_id, title, views FROM episodes 
            WHERE movie_code = ? AND episode_number = ?
            """,
            (movie_code.strip(), int(episode_number))
        ) as cursor:
            ep = await cursor.fetchone()
            if ep:
                await db.execute("UPDATE episodes SET views = views + 1 WHERE id = ?", (ep[0],))
                await db.commit()
                return {
                    "id": ep[0],
                    "movie_code": ep[1],
                    "episode_number": ep[2],
                    "file_id": ep[3],
                    "title": ep[4],
                    "views": ep[5] + 1
                }
            return None


async def delete_episode(movie_code: str, episode_number: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM episodes WHERE movie_code = ? AND episode_number = ?",
            (movie_code.strip(), int(episode_number))
        )
        await db.commit()
        return cursor.rowcount > 0


# ==================== KANALLAR ====================

async def add_channel(channel_id: str, channel_name: str, invite_link: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO channels (channel_id, channel_name, invite_link) VALUES (?, ?, ?)",
                (channel_id.strip(), channel_name, invite_link.strip())
            )
            await db.commit()
            return True
    except Exception:
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
