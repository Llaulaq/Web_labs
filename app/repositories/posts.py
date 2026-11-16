import sqlite3

from app.schemas import User


class PostRepository:
    """Посты: один JOIN-запрос вместо N+1."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, author_id: int, title: str, body: str = "") -> dict:
        cursor = self.conn.execute(
            "INSERT INTO posts (author_id, title, body) VALUES (?, ?, ?)",
            (author_id, title, body),
        )
        self.conn.commit()
        return {"id": cursor.lastrowid, "author_id": author_id, "title": title, "body": body}

    def list_with_author(self, author_id: int) -> list[dict]:
        """Посты автора с данными автора — один запрос с JOIN (нет N+1)."""
        rows = self.conn.execute(
            """
            SELECT p.id, p.title, p.body, u.id AS author_id, u.name AS author_name, u.email AS author_email
            FROM posts p
            JOIN users u ON u.id = p.author_id
            WHERE p.author_id = ?
            ORDER BY p.id
            """,
            (author_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_with_author_naive(self, author_id: int, users_repo) -> list[dict]:
        """Наивная версия: N+1 (для демонстрации в lab7/benchmark.py)."""
        posts = self.conn.execute(
            "SELECT id, title, body, author_id FROM posts WHERE author_id = ? ORDER BY id",
            (author_id,),
        ).fetchall()
        result = []
        for post in posts:  # отдельный запрос к users на КАЖДЫЙ пост
            author: User | None = users_repo.get(post["author_id"])
            result.append({**dict(post), "author_name": author.name if author else None,
                           "author_email": author.email if author else None})
        return result
