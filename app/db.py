import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 50),
    email TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL CHECK(age BETWEEN 18 AND 120),
    password_hash TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS revoked_tokens (
    jti TEXT PRIMARY KEY,
    revoked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Простая миграция: добавляет password_hash, если таблица users создана раньше."""
    columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
    if "password_hash" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''")
        conn.commit()


def connect(database_path: str) -> sqlite3.Connection:
    """Открывает соединение с SQLite, применяет схему и миграции."""
    path = Path(database_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
