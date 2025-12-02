import aiosqlite
from typing import Optional, Tuple, List
import logging

DB_PATH = "havan_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        # Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                tg_user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Invite links table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS invite_links (
                invite_link TEXT PRIMARY KEY,
                tg_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id)
            )
        ''')
        # Deduplicate invite_links by tg_user_id (keep the newest row)
        try:
            await conn.execute('''
                DELETE FROM invite_links
                WHERE rowid NOT IN (
                    SELECT MAX(rowid) FROM invite_links GROUP BY tg_user_id
                )
            ''')
        except Exception as e:
            logging.debug(f"Dedup invite_links skipped/failed: {e}")
        # Add unique index to enforce one link per user
        try:
            await conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS ux_invite_links_user ON invite_links(tg_user_id)
            ''')
        except Exception as e:
            logging.warning(f"Could not create unique index on invite_links(tg_user_id): {e}")

        # Join events table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS join_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_link TEXT NOT NULL,
                joined_user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invite_link) REFERENCES invite_links(invite_link)
            )
        ''')
        # Deduplicate join_events (keep the newest row per pair)
        try:
            await conn.execute('''
                DELETE FROM join_events
                WHERE rowid NOT IN (
                    SELECT MAX(rowid) FROM join_events GROUP BY invite_link, joined_user_id
                )
            ''')
        except Exception as e:
            logging.debug(f"Dedup join_events skipped/failed: {e}")
        # Prevent duplicate join rows per (invite_link, user)
        try:
            await conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS ux_join_events_unique ON join_events(invite_link, joined_user_id)
            ''')
        except Exception as e:
            logging.warning(f"Could not create unique index on join_events(invite_link, joined_user_id): {e}")

        # User topics table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_topics (
                tg_user_id INTEGER PRIMARY KEY,
                topic_id INTEGER UNIQUE NOT NULL,
                topic_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id)
            )
        ''')
        # Submissions table (if needed)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER NOT NULL,
                file_ids TEXT,
                caption TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                staff_handled BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id)
            )
        ''')
        await conn.commit()

# Repository methods
async def ensure_user(tg_user_id: int, username: Optional[str], first_name: Optional[str]):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('''
            INSERT INTO users (tg_user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name
        ''', (tg_user_id, username, first_name))
        await conn.commit()

async def get_invite_by_user(tg_user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT invite_link FROM invite_links WHERE tg_user_id = ?', (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_invite_link(invite_link: str, tg_user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        # Do not replace existing mapping to preserve a stable per-user link
        await conn.execute('INSERT OR IGNORE INTO invite_links (invite_link, tg_user_id, active) VALUES (?, ?, 1)', (invite_link, tg_user_id))
        await conn.commit()

async def get_user_join_count(tg_user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('''
            SELECT COUNT(*) FROM join_events je
            JOIN invite_links il ON je.invite_link = il.invite_link
            WHERE il.tg_user_id = ?
        ''', (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_rank(tg_user_id: int) -> Tuple[Optional[int], int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        # Get total users with invites
        cur = await conn.execute('''
            SELECT COUNT(DISTINCT tg_user_id) FROM invite_links
        ''')
        total_users = (await cur.fetchone())[0]

        # Get rank of this user
        cur = await conn.execute('''
            SELECT rank FROM (
                SELECT tg_user_id, ROW_NUMBER() OVER (ORDER BY (
                    SELECT COUNT(*) FROM join_events je
                    JOIN invite_links il ON je.invite_link = il.invite_link
                    WHERE il.tg_user_id = u.tg_user_id
                ) DESC) as rank
                FROM users u
                WHERE EXISTS (SELECT 1 FROM invite_links WHERE tg_user_id = u.tg_user_id)
            ) WHERE tg_user_id = ?
        ''', (tg_user_id,))
        row = await cur.fetchone()
        rank = row[0] if row else None
        return rank, total_users

async def get_invite_by_link(invite_link: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT invite_link FROM invite_links WHERE invite_link = ? AND active = 1', (invite_link,))
        row = await cur.fetchone()
        return row[0] if row else None

async def record_join(invite_link: str, joined_user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        # Ignore duplicates if already recorded
        await conn.execute('INSERT OR IGNORE INTO join_events (invite_link, joined_user_id) VALUES (?, ?)', (invite_link, joined_user_id))
        await conn.commit()

async def get_user_topic(tg_user_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT topic_id FROM user_topics WHERE tg_user_id = ?', (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_user_topic(tg_user_id: int, topic_id: int, topic_name: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        # Use UPSERT to prevent duplicate rows per user and update mapping if needed
        await conn.execute('''
            INSERT INTO user_topics (tg_user_id, topic_id, topic_name)
            VALUES (?, ?, ?)
            ON CONFLICT(tg_user_id) DO UPDATE SET
                topic_id=excluded.topic_id,
                topic_name=excluded.topic_name
        ''' , (tg_user_id, topic_id, topic_name))
        await conn.commit()

async def get_user_by_topic(topic_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT tg_user_id FROM user_topics WHERE topic_id = ?', (topic_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_submission(tg_user_id: int, file_ids: List[str], caption: Optional[str]):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            'INSERT INTO submissions (tg_user_id, file_ids, caption) VALUES (?, ?, ?)',
            (tg_user_id, ','.join(file_ids), caption or '')
        )
        await conn.commit()
        cur = await conn.execute('SELECT last_insert_rowid()')
        row = await cur.fetchone()
        return row[0] if row else None
