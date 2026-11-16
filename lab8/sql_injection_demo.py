"""Демонстрация SQL-инъекции: уязвимый vs параметризованный запрос (задание 2, занятие 11).

Запуск: .venv\\Scripts\\python lab8\\sql_injection_demo.py
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

DB = str(Path(tempfile.gettempdir()) / "web_labs_sqli.db")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.executescript("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
INSERT INTO users (id, email, password_hash) VALUES
    (1, 'admin@example.com', 'pbkdf2$...'),
    (2, 'user@example.com', 'pbkdf2$...');
""")


def login_vulnerable(email: str, _password: str) -> bool:
    """УЯЗВИМО: строка подставляется прямо в SQL."""
    query = f"SELECT * FROM users WHERE email = '{email}'"
    print(f"  SQL: {query}")
    return conn.execute(query).fetchone() is not None


def login_safe(email: str, _password: str) -> bool:
    """ЗАЩИЩЁН: параметризованный запрос."""
    query = "SELECT * FROM users WHERE email = ?"
    print(f"  SQL: {query}  параметры: ({email!r},)")
    return conn.execute(query, (email,)).fetchone() is not None


print("=== 1. Обход авторизации: ' OR '1'='1 ===")
payload = "' OR '1'='1"
print(f"уязвимый вариант:   вход {'РАЗРЕШЁН' if login_vulnerable(payload, 'x') else 'запрещён'}")
print(f"защищённый вариант: вход {'РАЗРЕШЁН' if login_safe(payload, 'x') else 'запрещён'}")

print("\n=== 2. Чужой аккаунт: admin@example.com'-- ===")
payload = "admin@example.com'--"
print(f"уязвимый вариант:   вход {'РАЗРЕШЁН' if login_vulnerable(payload, 'x') else 'запрещён'}")
print(f"защищённый вариант: вход {'РАЗРЕШЁН' if login_safe(payload, 'x') else 'запрещён'}")

print("\n=== 3. Удаление данных через UNION/DDL не сработает в SQLite-execute,")
print("    но в MySQL/PostgreSQL classic payload: '; DROP TABLE users;--")
print("    Защита та же: параметризованные запросы + минимальные права БД (нет DROP).")

conn.close()
Path(DB).unlink(missing_ok=True)
