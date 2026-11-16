"""Демонстрация для лабораторной 7: транзакции, гонки, N+1, индексы.

Запуск: .venv\\Scripts\\python lab7\\benchmark.py
Создаёт временную БД в папке временных файлов и удаляет её после прогона.
"""
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import connect  # noqa: E402
from app.repositories.accounts import AccountRepository, InsufficientFunds  # noqa: E402
from app.repositories.posts import PostRepository  # noqa: E402
from app.repositories.users import UserRepository  # noqa: E402
from app.schemas import UserCreate  # noqa: E402

DB = str(Path(tempfile.gettempdir()) / "web_labs_bench.db")


def seed(conn, users=50, posts_per_user=200):
    conn.execute("DELETE FROM posts")
    conn.execute("DELETE FROM accounts")
    conn.execute("DELETE FROM users")
    users_repo = UserRepository(conn)
    posts_repo = PostRepository(conn)
    for i in range(users):
        cursor = conn.execute(
            "INSERT INTO users (name, email, age, password_hash) VALUES (?, ?, ?, ?)",
            (f"User {i}", f"user{i}@example.com", 25 + i % 60, "pbkdf2$ZGV2$ZGV2"),
        )
        uid = cursor.lastrowid
        for j in range(posts_per_user):
            posts_repo.create(uid, f"Post {j} of user {i}")
    conn.commit()
    print(f"Сгенерировано: {users} пользователей, {users * posts_per_user} постов")


def demo_race():
    print("\n=== 1. Конкурентные переводы (10 потоков x 100 переводов по 1) ===")
    conn = connect(DB)
    accounts = AccountRepository(conn)
    ids = [row[0] for row in conn.execute("SELECT id FROM users ORDER BY id LIMIT 2")]
    src, dst = ids[0], ids[1]
    accounts.create(src, balance=1000)
    accounts.create(dst, balance=0)
    errors = []

    def worker():
        c = connect(DB)  # каждый поток — своё соединение
        repo = AccountRepository(c)
        for _ in range(100):
            for _attempt in range(5):  # retry при "database is locked"
                try:
                    repo.transfer(src, dst, 1)
                    break
                except InsufficientFunds:
                    break
                except sqlite3.OperationalError:
                    time.sleep(0.005)
            else:
                errors.append(RuntimeError("Не удалось выполнить перевод за 5 попыток"))
        c.close()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    b1 = accounts.get(src)["balance"]
    b2 = accounts.get(dst)["balance"]
    print(f"  выполнено за {elapsed:.2f} с, ошибок: {len(errors)}")
    print(f"  балансы: {src} = {b1}, {dst} = {b2}, сумма = {b1 + b2}")
    assert b1 + b2 == 1000, "ПОТЕРЯННОЕ ОБНОВЛЕНИЕ: сумма балансов изменилась!"
    assert b1 >= 0, "Баланс ушёл в минус!"
    print("  [OK] атомарность выдержана: сумма не изменилась, баланс неотрицателен")


def demo_n_plus_one():
    print("\n=== 2. N+1 против JOIN (посты одного автора) ===")
    conn = connect(DB)
    posts = PostRepository(conn)
    users_repo = UserRepository(conn)
    author_id = conn.execute("SELECT MIN(author_id) FROM posts").fetchone()[0]

    t0 = time.perf_counter()
    naive = posts.list_with_author_naive(author_id, users_repo)
    t_naive = time.perf_counter() - t0

    t0 = time.perf_counter()
    join = posts.list_with_author(author_id)
    t_join = time.perf_counter() - t0

    assert len(naive) == len(join)
    print(f"  N+1 (запросов: 1 + {len(naive)}): {t_naive * 1000:.1f} мс")
    print(f"  JOIN (запросов: 1):                 {t_join * 1000:.1f} мс")
    print(f"  ускорение: {t_naive / max(t_join, 1e-9):.0f}x")


def demo_index():
    print("\n=== 3. Индекс и EXPLAIN QUERY PLAN ===")
    conn = connect(DB)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    def plan(query, args):
        return [row[3] for row in conn.execute(f"EXPLAIN QUERY PLAN {query}", args)]

    q = "SELECT * FROM users WHERE age = ?"
    conn.execute("DROP INDEX IF EXISTS idx_users_age")
    print(f"  {q}")
    print(f"    без индекса:   {plan(q, (30,))}")
    conn.execute("CREATE INDEX idx_users_age ON users(age)")
    print(f"    с индексом:    {plan(q, (30,))}")

    # LIKE '%...%' не использует обычный B-tree индекс
    q2 = "SELECT * FROM users WHERE name LIKE ?"
    print(f"  {q2} с параметром '%ser 7%'")
    print(f"    план: {plan(q2, ('%ser 7%',))}  ← SCAN: ведущий % не даёт использовать индекс")

    q3 = "SELECT COUNT(*) FROM posts WHERE author_id = ?"
    print(f"  {q3}")
    author_id = conn.execute("SELECT MIN(author_id) FROM posts").fetchone()[0]
    print(f"    план: {plan(q3, (author_id,))}")


if __name__ == "__main__":
    conn = connect(DB)
    seed(conn)
    demo_race()
    demo_n_plus_one()
    demo_index()
    conn.close()
    try:
        Path(DB).unlink(missing_ok=True)
    except PermissionError:
        print("(временный файл БД будет удалён ОС позже)")
    print("\nГотово.")
