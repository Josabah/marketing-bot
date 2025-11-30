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
            INSERT OR IGNORE INTO users (tg_user_id, username, first_name) VALUES (?, ?, ?)
        ''', (tg_user_id, username, first_name))
        await conn.commit()

async def get_invite_by_user(tg_user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT invite_link FROM invite_links WHERE tg_user_id = ?', (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_invite_link(invite_link: str, tg_user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('INSERT OR REPLACE INTO invite_links (invite_link, tg_user_id, active) VALUES (?, ?, 1)', (invite_link, tg_user_id))
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
        await conn.execute('INSERT INTO join_events (invite_link, joined_user_id) VALUES (?, ?)', (invite_link, joined_user_id))
        await conn.commit()

async def get_user_topic(tg_user_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute('SELECT topic_id FROM user_topics WHERE tg_user_id = ?', (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_user_topic(tg_user_id: int, topic_id: int, topic_name: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('INSERT INTO user_topics (tg_user_id, topic_id, topic_name) VALUES (?, ?, ?)', (tg_user_id, topic_id, topic_name))
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
