import sqlite3

from app.schemas import User, UserCreate, UserUpdate


class UserRepository:
    """Слой доступа к данным: только SQL, без бизнес-логики."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list(self, skip: int, limit: int, search: str | None) -> tuple[int, list[User]]:
        if search:
            needle = f"%{search}%"
            where = "WHERE name LIKE ? OR email LIKE ?"
            args: tuple = (needle, needle)
        else:
            where, args = "", ()
        total = self.conn.execute(f"SELECT COUNT(*) FROM users {where}", args).fetchone()[0]
        rows = self.conn.execute(
            f"SELECT id, name, email, age FROM users {where} ORDER BY id LIMIT ? OFFSET ?",
            (*args, limit, skip),
        ).fetchall()
        return total, [User(**row) for row in rows]

    def get(self, user_id: int) -> User | None:
        row = self.conn.execute(
            "SELECT id, name, email, age FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User(**row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self.conn.execute(
            "SELECT id, name, email, age FROM users WHERE email = ?", (email,)
        ).fetchone()
        return User(**row) if row else None

    def get_credentials(self, email: str) -> tuple[int, str, str] | None:
        """Возвращает (id, email, password_hash) для проверки логина."""
        row = self.conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        return (row["id"], row["email"], row["password_hash"]) if row else None

    def create(self, payload: UserCreate, password_hash: str) -> User:
        cursor = self.conn.execute(
            "INSERT INTO users (name, email, age, password_hash) VALUES (?, ?, ?, ?)",
            (payload.name, payload.email, payload.age, password_hash),
        )
        self.conn.commit()
        return self.get(cursor.lastrowid)

    def update(self, user_id: int, payload: UserUpdate) -> User | None:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return self.get(user_id)
        columns = ", ".join(f"{key} = ?" for key in data)
        self.conn.execute(
            f"UPDATE users SET {columns} WHERE id = ?", (*data.values(), user_id)
        )
        self.conn.commit()
        return self.get(user_id)

    def delete(self, user_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0
