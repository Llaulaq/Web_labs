import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 50),
    email TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL CHECK(age BETWEEN 18 AND 120)
);
"""


def connect(database_path: str) -> sqlite3.Connection:
    """Открывает соединение с SQLite и применяет миграции схемы."""
    path = Path(database_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
