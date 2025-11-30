# db.py
import aiosqlite
import asyncio
from datetime import datetime

DB_PATH = "havan_bot.db"

SCHEMA = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    tg_user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS invite_links (
    invite_link TEXT PRIMARY KEY,
    tg_user_id INTEGER,
    created_at TEXT,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (tg_user_id) REFERENCES users(tg_user_id)
);

CREATE TABLE IF NOT EXISTS join_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invite_link TEXT,
    joined_user_id INTEGER,
    joined_at TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_user_id INTEGER,
    file_ids TEXT, -- comma separated
    caption TEXT,
    created_at TEXT,
    staff_handled INTEGER DEFAULT 0
);
"""

async def init_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.executescript(SCHEMA)
    await db.commit()
    await db.close()

async def ensure_user(tg_user_id, username=None, first_name=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT tg_user_id FROM users WHERE tg_user_id = ?", (tg_user_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO users (tg_user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
                (tg_user_id, username, first_name, datetime.utcnow().isoformat())
            )
            await db.commit()

async def save_invite_link(invite_link, tg_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO invite_links (invite_link, tg_user_id, created_at, active) VALUES (?, ?, ?, 1)",
            (invite_link, tg_user_id, datetime.utcnow().isoformat())
        )
        await db.commit()

async def get_invite_by_user(tg_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT invite_link FROM invite_links WHERE tg_user_id = ? AND active = 1", (tg_user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def get_invite_by_link(invite_link):
    """Check if an invite link exists in our database (was created by this bot)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT invite_link FROM invite_links WHERE invite_link = ? AND active = 1", (invite_link,))
        row = await cur.fetchone()
        return row[0] if row else None

async def record_join(invite_link, joined_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO join_events (invite_link, joined_user_id, joined_at) VALUES (?, ?, ?)",
            (invite_link, joined_user_id, datetime.utcnow().isoformat())
        )
        await db.commit()

async def get_user_join_count(tg_user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM join_events je JOIN invite_links il ON je.invite_link = il.invite_link WHERE il.tg_user_id = ?",
            (tg_user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_rank(tg_user_id, limit=100):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT il.tg_user_id, COUNT(je.id) AS cnt FROM invite_links il LEFT JOIN join_events je ON il.invite_link = je.invite_link GROUP BY il.tg_user_id ORDER BY cnt DESC"
        )
        rows = await cur.fetchall()
        rank = None
        for idx, r in enumerate(rows, start=1):
            if r[0] == tg_user_id:
                rank = idx
                break
        total = len(rows)
        return rank, total

async def save_submission(tg_user_id, file_ids, caption):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO submissions (tg_user_id, file_ids, caption, created_at) VALUES (?, ?, ?, ?)",
            (tg_user_id, ",".join(file_ids), caption or "", datetime.utcnow().isoformat())
        )
        await db.commit()
        cur = await db.execute("SELECT last_insert_rowid()")
        row = await cur.fetchone()
        return row[0]
